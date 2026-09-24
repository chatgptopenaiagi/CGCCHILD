import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cgcchild.live import adapter
from cgcchild.live.redaction import redact
from cgcchild.live.protocol import make_event, validate_event, ZERO_HASH


def request(method, params=None, identifier=1):
    value = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        value["params"] = params
    if identifier is not None:
        value["id"] = identifier
    return adapter.wire(value)


def initialize():
    return request("initialize", {"protocolVersion": adapter.PROTOCOL, "capabilities": {},
                                 "clientInfo": {"name": "owned-test", "version": "1"}})


class FakeSession:
    path = Path("C:/owned-fixture/sessions/id")

    def __init__(self):
        self.reported = []

    def summary(self):
        return dict(session_id="owned-session", generation=1, state="RUNNING",
                    project_root="C:/owned-fixture/project", event_count=len(self.reported),
                    checkpoint_count=0, unfinished_work=["Private notes excluded from compact status"])

    def report(self, event_type, payload, actor="Codex", correlation_id=None):
        self.reported.append((event_type, redact(payload), actor, correlation_id))
        return dict(event_id="event-1", sequence=len(self.reported), evidence_grade="REPORTED",
                    reconciliation_state="UNKNOWN")


class LiveAdapterTests(unittest.TestCase):
    def ready(self, session=None):
        peer = adapter.LiveMCPAdapter(session or FakeSession())
        self.assertIn("result", json.loads(peer.handle(initialize())))
        self.assertIsNone(peer.handle(request("notifications/initialized", identifier=None)))
        return peer

    def test_all_reports_are_claims_and_no_executor_is_advertised(self):
        peer = self.ready()
        tools = json.loads(peer.handle(request("tools/list")))["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, {*adapter.TOOLS, adapter.STATUS_TOOL})
        for tool in tools:
            self.assertEqual(tool["annotations"]["readOnlyHint"], tool["name"] == adapter.STATUS_TOOL)
            self.assertFalse(tool["annotations"]["destructiveHint"])
        for name in adapter.TOOLS:
            response = peer.handle(request("tools/call", {"name": name, "arguments": {"payload": {"text": "fact"}}}))
            result = json.loads(response)["result"]
            self.assertFalse(result["isError"])
            self.assertEqual(result["structuredContent"]["evidence_grade"], "REPORTED")
            self.assertEqual(result["structuredContent"]["reconciliation_state"], "UNKNOWN")
            self.assertFalse(result["structuredContent"]["mutation_authorized"])

    def test_no_grade_actor_event_or_command_escalation(self):
        peer = self.ready()
        for arguments in ({"payload": {}, "evidence_grade": "VERIFIED"},
                          {"payload": {}, "actor": "CGC"}, {"payload": {}, "source": "GIT"},
                          {"payload": {}, "event_type": "PUSH_VERIFIED"}):
            result = json.loads(peer.handle(request("tools/call", {
                "name": "cgc_live_push_reported", "arguments": arguments})))["result"]
            self.assertTrue(result["isError"])
        for name in ("shell", "execute", "cgc_live_push_verified", "cgc_live_run_test", "cgc_live_launch"):
            self.assertTrue(json.loads(peer.handle(request("tools/call", {"name": name,
                                         "arguments": {"payload": {}}})))["result"]["isError"])
        self.assertEqual(peer.session.reported, [])

    def test_nested_labels_do_not_promote_and_secret_payload_is_sanitized(self):
        peer = self.ready()
        result = peer.dispatch("cgc_live_command_report", {"payload": {
            "evidence_grade": "VERIFIED", "password": "synthetic-secret", "text": "sk-proj-synthetic0123456789"}})
        self.assertEqual(result["evidence_grade"], "REPORTED")
        self.assertEqual(peer.session.reported[0][1]["password"], "[REDACTED]")
        self.assertNotIn("synthetic0123456789", json.dumps(peer.session.reported))

    def test_status_is_compact_and_contains_no_unfinished_notes(self):
        value = self.ready().dispatch(adapter.STATUS_TOOL, {})
        self.assertNotIn("unfinished_work", value)
        self.assertNotIn("project_root", value)
        self.assertEqual(value["lifecycle_hooks"], "NOT_INSTALLED")

    def test_initialization_and_duplicate_notification_refuse(self):
        peer = adapter.LiveMCPAdapter(FakeSession())
        self.assertIn("error", json.loads(peer.handle(request("tools/list"))))
        peer.handle(initialize())
        self.assertIn("error", json.loads(peer.handle(request("tools/list"))))
        peer.handle(request("notifications/initialized", identifier=None))
        peer.handle(request("notifications/initialized", identifier=None))
        self.assertIn("error", json.loads(peer.handle(request("tools/list"))))

    def test_hostile_frames_and_identifiers(self):
        peer = self.ready()
        frames = [b"[]\n", b"\xff\n", b'{"id":1,"id":2}\n', b'NaN\n',
                  request("ping", identifier=True), request("ping", identifier=2**54),
                  request("ping", identifier="a\n"), request("tools/list", params=[]),
                  b"x" * (adapter.MAX_FRAME + 1)]
        for raw in frames:
            self.assertIn("error", json.loads(peer.handle(raw)))

    def test_stream_is_finite_and_oversized_frame_stops(self):
        source = io.BytesIO(initialize() + request("notifications/initialized", identifier=None) + request("ping") * 5)
        target = io.BytesIO()
        self.assertEqual(adapter.serve(FakeSession(), source, target, max_messages=3), 0)
        self.assertEqual(len(target.getvalue().splitlines()), 2)
        self.assertTrue(source.read())
        self.assertEqual(adapter.serve(FakeSession(), io.BytesIO(b"x" * (adapter.MAX_FRAME + 1)), io.BytesIO()), 2)
        for limit in (True, 0, adapter.MAX_MESSAGES + 1):
            with self.assertRaises(ValueError):
                adapter.serve(FakeSession(), io.BytesIO(), io.BytesIO(), max_messages=limit)

    def test_failure_message_does_not_echo_os_or_payload(self):
        session = FakeSession()
        with patch.object(session, "report", side_effect=OSError("sensitive-detail")):
            response = self.ready(session).handle(request("tools/call", {"name": "cgc_live_push_reported",
                                                    "arguments": {"payload": {"text": "private-note"}}}))
        self.assertNotIn(b"sensitive-detail", response)
        self.assertNotIn(b"private-note", response)
        self.assertTrue(json.loads(response)["result"]["isError"])

    @unittest.skipUnless(os.name == "nt", "Windows native launcher")
    def test_managed_launcher_exact_exe_cwd_and_ephemeral_metadata(self):
        session = FakeSession()
        with tempfile.TemporaryDirectory() as directory:
            exe = Path(directory) / "owned-codex.exe"
            exe.write_bytes(b"fixture only; never executed")
            with patch.object(adapter.subprocess, "Popen") as popen:
                popen.return_value.pid = 123
                result = adapter.launch_codex(session, exe)
            args, kwargs = popen.call_args
            self.assertEqual(args[0], [str(exe.resolve())])
            self.assertEqual(kwargs["cwd"], session.summary()["project_root"])
            self.assertEqual(kwargs["env"]["CGC_SESSION_DIR"], str(session.path))
            self.assertEqual(kwargs["env"]["CGC_SESSION_GENERATION"], "1")
            self.assertNotIn("shell", kwargs)
            self.assertEqual(result["task_result"], "UNKNOWN")
            cmd = Path(directory) / "codex.cmd"
            cmd.write_text("not executed")
            with self.assertRaisesRegex(ValueError, "CODEX_EXE_REQUIRED"):
                adapter.launch_codex(session, cmd)

    @unittest.skipUnless(os.name == "nt", "Windows native launcher")
    def test_missing_codex_keeps_observer_available(self):
        with patch.object(adapter.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ValueError, "CODEX_EXECUTABLE_UNAVAILABLE"):
                adapter.launch_codex(FakeSession())


class ProtocolBoundaryTests(unittest.TestCase):
    def test_malformed_enum_types_have_controlled_refusal(self):
        event = make_event("session", "project", 1, ZERO_HASH, "COMMAND_REPORTED", {}, grade="REPORTED")
        for field in ("event_type", "evidence_grade", "reconciliation_state"):
            for value in ([], {}, 42, None):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validate_event(dict(event, **{field: value}), ZERO_HASH, 1, "session")
        for options in ({"event_type": []}, {"grade": {}}, {"state": []}):
            args = dict(event_type="COMMAND_REPORTED", grade="REPORTED", state="UNKNOWN")
            args.update(options)
            with self.subTest(options=options), self.assertRaises(ValueError):
                make_event("session", "project", 1, ZERO_HASH, payload={}, **args)


if __name__ == "__main__":
    unittest.main()
