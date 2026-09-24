"""Q1/Q3-Q5: actual Windows evidence sessions and interruption boundaries."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from cgcchild.live import Session, open_capsule, discover_sessions
from cgcchild.live.protocol import canonical, decode, make_event, validate_event, sha, ZERO_HASH
from cgcchild.live.redaction import redact
from cgcchild.live.journal import Journal


class ProtocolTests(unittest.TestCase):
    def event(self, **kwargs):
        return make_event("session", "project", 1, ZERO_HASH, "COMMAND_REPORTED", {"text": "test"}, **kwargs)

    def test_chain_binds_all_fields_and_payload(self):
        event = self.event()
        validate_event(event, ZERO_HASH, 1, "session")
        for field, value in (("actor", "other"), ("sequence", 2), ("payload", {"text": "changed"}), ("event_sha256", ZERO_HASH)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_event(dict(event, **{field: value}), ZERO_HASH, 1, "session")

    def test_reported_and_reconciliation_are_orthogonal(self):
        event = self.event(grade="REPORTED", state="CONTRADICTED")
        self.assertEqual(event["evidence_grade"], "REPORTED")
        self.assertIsNone(event["verified_at"])
        self.assertEqual(event["reconciliation_state"], "CONTRADICTED")

    def test_bounds_duplicate_nonfinite_depth(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.assertRaises(ValueError): decode(raw)
        value = {}
        for _ in range(12): value = {"x": value}
        with self.assertRaises(ValueError): redact(value)
        with self.assertRaises(ValueError): self.event(correlation_id="x" * 129)
        with self.assertRaises(ValueError): self.event(grade="TRUST_ME")

    def test_redaction_minimizes_credentials_and_reasoning(self):
        dummy = "ghp_" + "EXAMPLEONLY" * 4
        value = redact({"token": dummy, "hidden_reasoning": "do not retain", "environment": {"PATH": "x"},
                        "note": "password=fictional " + dummy + " Authorization: Bearer fictionalvalue",
                        "private_key": "-----BEGIN PRIVATE KEY-----\nfictional\n-----END PRIVATE KEY-----"})
        encoded = canonical(value)
        for secret in (dummy, "do not retain", "fictional", "PATH"):
            self.assertNotIn(secret.encode(), encoded)
        event = self.event(correlation_id=dummy)
        self.assertNotIn(dummy, event["correlation_id"])
        command = redact({"command": ["tool.exe", "--password", "plain_value_without_token_shape",
                                     "--api-key", "another_plain_value", "--token=fictional_value"]})
        for value in ("plain_value_without_token_shape", "another_plain_value", "fictional_value"):
            self.assertNotIn(value.encode(), canonical(command))
        self.assertEqual(command["command"][:2], ["tool.exe", "--password"])


@unittest.skipUnless(os.name == "nt", "Windows mission")
class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cgc-live-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project, self.store = self.root / "project", self.root / "sessions"
        self.project.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "CGC Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.project / "a.txt").write_text("start")
        self.git("add", "a.txt")
        self.git("commit", "-m", "fixture initial")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.project, stderr=subprocess.PIPE, text=True).strip()

    def session(self):
        return Session.start(self.project, self.store)

    def test_full_real_session_contradiction_test_commit_checkpoint_capsule(self):
        session = self.session()
        before = (self.project / ".git" / "index").read_bytes()
        self.assertEqual(session.summary()["state"], "RUNNING")
        self.assertEqual(before, (self.project / ".git" / "index").read_bytes())
        report = session.report("FILE_EDIT_REPORTED", {"paths": ["a.txt"]})
        session.report("COMMAND_REPORTED", {"working_tree_clean": True})
        (self.project / "a.txt").write_text("modified")
        session.observe()
        self.assertEqual(session.summary()["files_changed"], 1)
        self.assertEqual(len(session.summary()["contradictions"]), 1)
        supported = [e for e in session.events() if e["event_type"] == "EVIDENCE_RECONCILED"]
        self.assertTrue(any(e["payload"]["report_event_id"] == report["event_id"] for e in supported))
        (self.project / "test_sample.py").write_text("import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertEqual(2+2,4)\n")
        result = session.run_test([sys.executable, "-m", "unittest", "test_sample"], "unittest")
        self.assertEqual(result["verification_state"], "VERIFIED_PASS")
        session.report("ERROR_OBSERVED", {"error_id": "e1", "text": "fixture problem"})
        session.report("ERROR_RESOLVED", {"error_id": "e1"})
        session.report("ERROR_REOPENED", {"error_id": "e1"})
        session.report("DECISION_DECLARED", {"text": "Keep historical authority separate"})
        session.report("UNFINISHED_WORK_DECLARED", {"text": "Clean Windows VM acceptance"})
        session.report("NEXT_ACTION_DECLARED", {"text": "Validate clean VM", "status": "EXECUTED"})
        self.git("add", ".")
        self.git("commit", "-m", "fixture change")
        head = self.git("rev-parse", "HEAD")
        session.report("COMMIT_REPORTED", {"sha": head})
        session.observe()
        self.assertTrue(any(e["event_type"] == "COMMIT_VERIFIED" for e in session.events()))
        session.checkpoint()
        self.assertEqual(session.summary()["checkpoint_count"], 1)
        capsule = session.preserve()
        imported = open_capsule(capsule)
        self.assertEqual(imported["authority"], "HISTORICAL_ONLY")
        self.assertFalse(imported["mutation_authorized"])
        self.assertTrue(imported["session"]["preservation_complete"])
        self.assertEqual(imported["session"]["open_errors"], 1)
        self.assertEqual(imported["next_action"]["status"], "UNEXECUTED_FUTURE_ACTION")
        self.assertEqual(len(imported["session"]["contradictions"]), 1)
        with self.assertRaises(ValueError): session.report("DECISION_DECLARED", {"text": "late"})
        process = subprocess.run([sys.executable, "-m", "cgcchild", "live", "open", "--input", str(capsule)], capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["authority"], "HISTORICAL_ONLY")

    def test_report_poisoning_cannot_break_durable_history(self):
        session = self.session()
        count = session.summary()["event_count"]
        for payload in ({"error_id": []}, {"test_id": {}}, {"paths": [42]}, {"text": 99}):
            with self.assertRaises(ValueError): session.report("ERROR_OBSERVED", payload)
        self.assertEqual(session.summary()["event_count"], count)
        with self.assertRaises(ValueError): session.report("PUSH_VERIFIED", {"sha": "x"})
        report = session.report("SESSION_ENDING", {"transition": {"from": "RUNNING", "to": "PRESERVED"}})
        self.assertEqual(report["evidence_grade"], "REPORTED")
        self.assertEqual(session.summary()["state"], "RUNNING")

    def test_storage_must_be_external_and_source_contents_not_captured(self):
        with self.assertRaises(ValueError): Session.start(self.project, self.project / "data")
        secret_source = "source_contents_must_never_be_in_journal"
        (self.project / "ordinary.txt").write_text(secret_source)
        session = self.session()
        session.observe()
        self.assertNotIn(secret_source.encode(), b"".join(p.read_bytes() for p in session.path.glob("events-*.jsonl")))

    def test_torn_tail_recovery_preserves_prefix_and_new_generation(self):
        session = self.session()
        path = sorted(session.path.glob("events-*.jsonl"))[-1]
        prefix = path.read_bytes()
        with path.open("ab") as stream: stream.write(b'{"incomplete":')
        reopened = Session.open(session.path)
        self.assertEqual(reopened.summary()["journal_integrity"], "TORN_TAIL")
        with self.assertRaises(ValueError): reopened.observe()
        assessment = reopened.recover()
        self.assertEqual(assessment["torn_tail"]["bytes"], 14)
        self.assertTrue(path.read_bytes().startswith(prefix))
        self.assertTrue(list(session.path.glob("torn-tail-*.bin")))
        self.assertEqual(reopened.resume()["generation"], 2)
        self.assertFalse(reopened.summary()["mutation_authorized"])

    def test_corruption_is_refused_not_repaired(self):
        session = self.session()
        path = sorted(session.path.glob("events-*.jsonl"))[0]
        raw = path.read_bytes().replace(b'"actor":"CGC"', b'"actor":"BAD"', 1)
        path.write_bytes(raw)
        with self.assertRaises(ValueError): Session.open(session.path)
        self.assertEqual(discover_sessions(self.store)[0]["journal_integrity"], "INVALID")

    def test_segment_rotation_chain_and_capacity_refusal(self):
        session = self.session()
        with patch("cgcchild.live.journal.MAX_SEGMENT_BYTES", 1024):
            for i in range(3): session.report("DECISION_DECLARED", {"text": str(i)})
        events = session.events()
        self.assertGreater(len(list(session.path.glob("events-*.jsonl"))), 1)
        self.assertEqual(events[-1]["previous_event_sha256"], events[-2]["event_sha256"])
        with patch("cgcchild.live.journal.MAX_EVENTS", len(events)):
            with self.assertRaises(ValueError): session.report("DECISION_DECLARED", {"text": "refused"})
        self.assertEqual(len(session.events()), len(events))

    def test_actual_killed_foreground_observer_releases_writer_and_recovers(self):
        session = self.session()
        code = "from cgcchild.live import Session; import sys,time; s=Session.open(sys.argv[1]); ctx=s.journal.writer(); ctx.__enter__(); print('LOCKED',flush=True); time.sleep(30)"
        process = subprocess.Popen([sys.executable, "-u", "-c", code, str(session.path)], stdout=subprocess.PIPE)
        try:
            self.assertEqual(process.stdout.readline().strip(), b"LOCKED")
            with self.assertRaises(ValueError): session.checkpoint()
            process.kill()
            process.wait(timeout=5)
            reopened = Session.open(session.path)
            reopened.recover()
            self.assertEqual(reopened.resume()["generation"], 2)
            reopened.checkpoint()
        finally:
            if process.poll() is None: process.kill(); process.wait(timeout=5)
            process.stdout.close()

    def test_incomplete_checkpoint_and_git_change_reconciled(self):
        session = self.session()
        with session._writer(): session._transition("CHECKPOINTING", "CHECKPOINT_STARTED")
        (self.project / "new.txt").write_text("later")
        self.git("add", ".")
        self.git("commit", "-m", "later fixture")
        reopened = Session.open(session.path)
        self.assertTrue(reopened.recover()["git_changed"])
        self.assertEqual(reopened.resume()["generation"], 2)
        self.assertEqual(reopened.summary()["checkpoint_count"], 0)

    def test_missing_final_capsule_is_recovery_candidate(self):
        session = self.session()
        with patch("cgcchild.live.capsule.build_capsule", side_effect=ValueError("SIMULATED_POWER_LOSS")):
            with self.assertRaises(ValueError): session.preserve()
        reopened = Session.open(session.path)
        self.assertTrue(reopened.summary()["needs_recovery"])
        reopened.resume()
        self.assertTrue(open_capsule(reopened.preserve())["session"]["preservation_complete"])

    def test_capsule_checks_projection_and_paths_without_extraction(self):
        capsule = self.session().preserve()
        raw = capsule.read_bytes()
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        session = decode(members["session.json"])
        session["tests"] = 42
        members["session.json"] = canonical(session)
        manifest = decode(members["manifest.json"])
        manifest["members"]["session.json"] = {"bytes": len(members["session.json"]), "sha256": sha(members["session.json"])}
        members["manifest.json"] = canonical(manifest)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, value in members.items(): archive.writestr(name, value)
        with self.assertRaises(ValueError): open_capsule(buffer.getvalue())


if __name__ == "__main__": unittest.main()
