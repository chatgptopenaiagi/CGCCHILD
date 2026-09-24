import json
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from cgcchild import sdk
from cgcchild.live.protocol import canonical, sha
from test_live_adapter import initialize, request


@unittest.skipUnless(os.name == "nt", "Windows live product interfaces")
class LiveInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.project = self.folder / "project"
        self.project.mkdir()
        self.store = self.folder / "sessions"
        self.git("init", "--initial-branch=main")
        self.git("config", "user.name", "Owned Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.project / "readme.txt").write_text("owned fixture")
        self.git("add", "readme.txt")
        self.git("commit", "-m", "Owned fixture baseline")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.project), *args], capture_output=True,
                              timeout=10, check=True)

    def cli(self, *args, input=None, check=True):
        run = subprocess.run([sys.executable, "-B", "-m", "cgcchild", "live", *map(str, args)],
                             input=input, capture_output=True, timeout=30)
        if check:
            self.assertEqual(run.returncode, 0, run.stderr.decode("utf-8", "replace"))
        return run

    def start(self):
        value = json.loads(self.cli("start", "--project", self.project, "--store", self.store).stdout)
        self.assertEqual(value["state"], "RUNNING")
        return Path(value["storage_location"])

    def test_fresh_process_cli_observe_test_checkpoint_capsule(self):
        session = self.start()
        self.cli("report", "--session", session, "--event-type", "COMMAND_REPORTED",
                 "--payload", '{"working_tree_clean":true}')
        (self.project / "readme.txt").write_text("owned edit")
        observed = json.loads(self.cli("observe", "--session", session).stdout)
        self.assertTrue(observed["changes"])
        (self.project / "test_owned.py").write_text("import unittest\nclass T(unittest.TestCase):\n def test_owned(self): self.assertEqual(1,1)\n")
        tested = json.loads(self.cli("test", "--session", session, "--framework", "unittest", "--timeout", "120", "--",
                                    sys.executable, "-m", "unittest", "test_owned").stdout)
        self.assertEqual(tested["verification_state"], "VERIFIED_PASS")
        checkpoint = json.loads(self.cli("checkpoint", "--session", session).stdout)
        self.assertEqual(checkpoint["checkpoint_count"], 1)
        self.assertTrue(checkpoint["contradictions"])
        end = json.loads(self.cli("end", "--session", session).stdout)
        capsule = json.loads(self.cli("open", "--input", end["capsule"]).stdout)
        self.assertEqual(capsule["authority"], "HISTORICAL_ONLY")
        self.assertFalse(capsule["mutation_authorized"])
        self.assertEqual(capsule["session"]["state"], "PRESERVED")
        self.assertEqual((self.project / "readme.txt").read_text(), "owned edit")
        refused = self.cli("report", "--session", session, "--event-type", "PUSH_REPORTED",
                           "--payload", "{}", check=False)
        self.assertEqual(refused.returncode, 2)

    def test_real_mcp_stdio_appends_report_and_refuses_promotion(self):
        session = self.start()
        frames = initialize() + request("notifications/initialized", identifier=None)
        frames += request("tools/call", {"name": "cgc_live_push_reported", "arguments": {
            "payload": {"sha": "a" * 40, "token": "synthetic-secret"}}}, identifier=2)
        frames += request("tools/call", {"name": "cgc_live_push_verified", "arguments": {"payload": {}}}, identifier=3)
        frames += request("tools/call", {"name": "cgc_live_error_observed", "arguments": {"payload": {"error_id": []}}}, identifier=4)
        run = self.cli("serve", "--session", session, input=frames)
        responses = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(len(responses), 4)
        self.assertEqual(responses[1]["result"]["structuredContent"]["evidence_grade"], "REPORTED")
        self.assertTrue(responses[2]["result"]["isError"])
        self.assertTrue(responses[3]["result"]["isError"])
        events = sdk.live_open(session).events()
        report = next(e for e in events if e["event_type"] == "PUSH_REPORTED")
        self.assertEqual(report["payload"]["token"], "[REDACTED]")
        self.assertFalse(any(e["event_type"] == "PUSH_VERIFIED" for e in events))
        self.assertEqual(sdk.live_open(session).summary()["state"], "RUNNING")

    def test_python_sdk_recovery_and_node_subprocess_facade(self):
        live = sdk.live_start(self.project, store=self.store)
        live.interrupt("owned crash simulation")
        self.cli("recover", "--session", live.path)
        resumed = json.loads(self.cli("resume", "--session", live.path).stdout)
        self.assertEqual(resumed["generation"], 2)
        code = """import assert from 'node:assert/strict';
import {LiveClient} from './sdk/javascript/index.mjs';
const c=new LiveClient({executable:process.argv[1],prefix:['-B','-m','cgcchild']});
assert.equal(c.status(process.argv[2]).generation,2);
const r=c.report(process.argv[2],'next_action_declared',{text:'Review owned fixture',status:'EXECUTED'});
assert.equal(r.evidence_grade,'REPORTED');
assert.equal(r.payload.status,'UNEXECUTED_FUTURE_ACTION');
assert.equal(c.checkpoint(process.argv[2]).checkpoint_count,1);
const p=c.preserve(process.argv[2]);
assert.equal(c.openCapsule(p.capsule).authority,'HISTORICAL_ONLY');
process.stdout.write('LIVE_NODE_INTEGRATION_PASSED');"""
        run = subprocess.run(["node", "--input-type=module", "-e", code, sys.executable, str(live.path)],
                             capture_output=True, timeout=45)
        self.assertEqual(run.returncode, 0, run.stderr.decode("utf-8", "replace"))
        self.assertEqual(run.stdout, b"LIVE_NODE_INTEGRATION_PASSED")
        sessions = sdk.live_sessions(self.store)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["state"], "PRESERVED")

    def test_bounded_foreground_watch_and_argument_failures(self):
        session = self.start()
        watched = json.loads(self.cli("watch", "--session", session, "--duration", 1,
                                      "--interval", 0.5, "--checkpoint-interval", 1).stdout)
        self.assertEqual(watched["state"], "WATCH_FINISHED")
        self.assertGreaterEqual(watched["session"]["checkpoint_count"], 1)
        for arguments in (("watch", "--duration", "0"), ("watch", "--duration", "1", "--interval", "nan"),
                          ("test",), ("report", "--event-type", "PUSH_REPORTED", "--payload", '{"a":1,"a":2}')):
            result = self.cli(arguments[0], "--session", session, *arguments[1:], check=False)
            self.assertEqual(result.returncode, 2)

    def test_malformed_journal_enum_cannot_crash_store_discovery(self):
        session = self.start()
        journal = sorted(session.glob("events-*.jsonl"))[0]
        lines = journal.read_bytes().splitlines(keepends=True)
        event = json.loads(lines[0])
        event["event_type"] = []
        lines[0] = canonical(event) + b"\n"
        journal.write_bytes(b"".join(lines))
        result = sdk.live_sessions(self.store)
        self.assertEqual(result[0]["journal_integrity"], "INVALID")
        self.assertEqual(result[0]["state"], "UNKNOWN")

    def test_hostile_capsule_shapes_and_historical_import_no_path_io(self):
        live = sdk.live_start(self.project, store=self.store)
        capsule = live.preserve()
        raw = capsule.read_bytes()
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            original = {name: archive.read(name) for name in archive.namelist()}
            first_info = archive.infolist()[0]

        def archive_bytes(members, compression=zipfile.ZIP_STORED):
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", compression=compression) as archive:
                for name, value in members.items():
                    archive.writestr(name, value)
            return buffer.getvalue()

        for manifest in ([], 42, None, "invalid"):
            members = dict(original, **{"manifest.json": canonical(manifest)})
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                sdk.live_capsule_open(archive_bytes(members))
        with self.assertRaises(ValueError):
            sdk.live_capsule_open(archive_bytes(original, zipfile.ZIP_BZIP2))
        damaged = bytearray(raw)
        offset = first_info.header_offset
        data_offset = offset + 30 + int.from_bytes(raw[offset + 26:offset + 28], "little") + int.from_bytes(raw[offset + 28:offset + 30], "little")
        damaged[data_offset] = 0x07  # Reserved DEFLATE block type.
        with self.assertRaises(ValueError):
            sdk.live_capsule_open(bytes(damaged))

        members = dict(original)
        timeline = json.loads(members["timeline.json"])
        event = timeline[-1]
        event["payload"]["transition"] = []
        event["payload_sha256"] = sha(canonical(event["payload"]))
        event["event_sha256"] = sha(event["previous_event_sha256"].encode("ascii") +
                                    canonical({k: v for k, v in event.items() if k != "event_sha256"}))
        members["timeline.json"] = canonical(timeline)
        index = json.loads(members["evidence-index.json"])
        index["last_event_sha256"] = event["event_sha256"]
        members["evidence-index.json"] = canonical(index)
        manifest = json.loads(members["manifest.json"])
        for name in manifest["members"]:
            manifest["members"][name] = {"bytes": len(members[name]), "sha256": sha(members[name])}
        members["manifest.json"] = canonical(manifest)
        with self.assertRaises(ValueError):
            sdk.live_capsule_open(archive_bytes(members))

        with patch.object(Path, "open", side_effect=AssertionError("historical path IO forbidden")), \
                patch.object(Path, "is_file", side_effect=AssertionError("historical path IO forbidden")), \
                patch.object(Path, "exists", side_effect=AssertionError("historical path IO forbidden")):
            historical = sdk.live_capsule_open(raw)
        self.assertEqual(historical["authority"], "HISTORICAL_ONLY")
        self.assertEqual(historical["current_authority"], "UNKNOWN")

    def test_corrupt_final_capsule_recovery_retains_artifact_and_new_generation(self):
        live = sdk.live_start(self.project, store=self.store)
        capsule = live.preserve()
        self.assertTrue(live.summary()["preservation_complete"])
        corrupted = b"owned fixture: incomplete final capsule"
        capsule.write_bytes(corrupted)
        reopened = sdk.live_open(live.path)
        self.assertFalse(reopened.summary()["preservation_complete"])
        self.assertTrue(reopened.summary()["needs_recovery"])
        self.assertTrue(sdk.live_sessions(self.store)[0]["recovery_candidate"])
        self.cli("recover", "--session", live.path)
        retained = capsule.with_name("interrupted-" + sha(corrupted) + ".cgcpack")
        self.assertEqual(retained.read_bytes(), corrupted)
        resumed = json.loads(self.cli("resume", "--session", live.path).stdout)
        self.assertEqual(resumed["generation"], 2)
        preserved = json.loads(self.cli("preserve", "--session", live.path).stdout)
        historical = sdk.live_capsule_open(preserved["capsule"])
        self.assertEqual(historical["session"]["generation"], 2)
        self.assertTrue(historical["session"]["preservation_complete"])
        self.assertEqual(retained.read_bytes(), corrupted)
        self.assertFalse(sdk.live_open(live.path).summary()["needs_recovery"])

    def test_cli_test_exit_codes_separate_failure_unknown_and_process_success(self):
        session = self.start()
        (self.project / "test_failure.py").write_text("import unittest\nclass T(unittest.TestCase):\n def test_failure(self): self.fail('owned fixture failure')\n")
        failed = self.cli("test", "--session", session, "--", sys.executable, "-m", "unittest", "test_failure", check=False)
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stdout)["verification_state"], "VERIFIED_FAIL")
        cases = (
            ("print('wrapper completed')", 2, "COMMAND_SUCCESS_TEST_COUNTS_UNKNOWN", 0),
            ("import sys; sys.exit(7)", 1, "COMMAND_FAILED_TEST_COUNTS_UNKNOWN", 7),
            ("print('Ran 0 tests in 0.001s\\n\\nOK')", 2, "NO_TESTS", 0),
            ("print('Ran 1 test in 0.001s\\n\\nFAILED (failures=1)')", 1, "CONTRADICTED", 0),
        )
        for script, exit_code, state, process_exit in cases:
            with self.subTest(state=state):
                run = self.cli("test", "--session", session, "--", sys.executable, "-c", script, check=False)
                self.assertEqual(run.returncode, exit_code)
                value = json.loads(run.stdout)
                self.assertEqual(value["verification_state"], state)
                self.assertEqual(value["exit_code"], process_exit)
        missing = self.cli("test", "--session", session, "--", self.project / "missing-owned-test.exe", check=False)
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(json.loads(missing.stdout)["verification_state"], "UNKNOWN")
        for timeout in ("0", "-1", "601", "nan", "inf"):
            with self.subTest(timeout=timeout):
                invalid = self.cli("test", "--session", session, "--timeout", timeout, "--", sys.executable,
                                   "-c", "print('must not execute')", check=False)
                self.assertEqual(invalid.returncode, 2)
                self.assertEqual(json.loads(invalid.stderr)["error"], "INVALID_TEST_TIMEOUT")
        self.assertEqual(sdk.live_open(session).summary()["state"], "RUNNING")


if __name__ == "__main__":
    unittest.main()
