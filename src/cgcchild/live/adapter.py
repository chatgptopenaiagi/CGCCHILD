"""Explicit Codex reports over bounded foreground MCP stdio.

Transport ownership is not source authentication. Reports never become observations
or verification merely because the caller used a named tool or a trusted process.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess

from cgcchild import __version__

PROTOCOL = "2025-11-25"
MAX_FRAME = 16 * 1024
MAX_RESPONSE = 128 * 1024
MAX_MESSAGES = 4096
REPORT_TYPES = {
    "session_started": "SESSION_STARTED",
    "command_report": "COMMAND_REPORTED",
    "file_edit_report": "FILE_EDIT_REPORTED",
    "test_started": "TEST_STARTED",
    "test_finished": "TEST_FINISHED",
    "error_observed": "ERROR_OBSERVED",
    "error_resolved": "ERROR_RESOLVED",
    "error_reopened": "ERROR_REOPENED",
    "decision_declared": "DECISION_DECLARED",
    "commit_reported": "COMMIT_REPORTED",
    "push_reported": "PUSH_REPORTED",
    "next_action_declared": "NEXT_ACTION_DECLARED",
    "unfinished_work_declared": "UNFINISHED_WORK_DECLARED",
    "session_finished": "SESSION_ENDING",
}
TOOLS = {"cgc_live_" + name: event for name, event in REPORT_TYPES.items()}
STATUS_TOOL = "cgc_live_status"


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def decode_request(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("DUPLICATE_FIELD")
            result[key] = value
        return result
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_FRAME or not raw.endswith(b"\n"):
        raise ValueError("INVALID_FRAME")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("INVALID_NUMBER")))


def error(identifier, code, message):
    return wire({"jsonrpc": "2.0", "id": identifier,
                 "error": {"code": code, "message": message}})


class LiveMCPAdapter:
    def __init__(self, session):
        self.session = session
        self.phase = "NEW"

    def dispatch(self, name, arguments):
        if type(arguments) is not dict:
            raise ValueError("INVALID_ARGUMENTS")
        if len(wire(arguments)) > MAX_FRAME:
            raise ValueError("ARGUMENT_LIMIT")
        if name == STATUS_TOOL:
            if arguments:
                raise ValueError("INVALID_ARGUMENTS")
            summary = self.session.summary()
            # Avoid large journal/history responses and accidental path/notes export.
            keys = ("session_id", "generation", "state", "event_count", "checkpoint_count",
                    "push_verification", "confidence", "current_confidence")
            return {**{k: summary[k] for k in keys if k in summary},
                    "storage_location": str(self.session.path),
                    "mutation_authorized": False, "report_truth": "REPORTED",
                    "lifecycle_hooks": "NOT_INSTALLED"}
        if name not in TOOLS or set(arguments) - {"payload", "correlation_id"} or "payload" not in arguments:
            raise ValueError("INVALID_ARGUMENTS")
        payload = arguments["payload"]
        correlation = arguments.get("correlation_id")
        if type(payload) is not dict or (correlation is not None and
                (type(correlation) is not str or not 1 <= len(correlation) <= 128)):
            raise ValueError("INVALID_ARGUMENTS")
        # Nested client labels are claims only; grade/source are set by Session.report.
        # No actor override, arbitrary event, state transition or executable is accepted.
        event = self.session.report(TOOLS[name], payload, actor="Codex", correlation_id=correlation)
        return {"event_id": event["event_id"], "sequence": event["sequence"],
                "evidence_grade": event["evidence_grade"],
                "reconciliation_state": event["reconciliation_state"],
                "mutation_authorized": False}

    def handle(self, raw):
        try:
            request = decode_request(raw)
        except (ValueError, UnicodeError, RecursionError):
            return error(None, -32700, "Parse error")
        if (type(request) is not dict or request.get("jsonrpc") != "2.0"
                or type(request.get("method")) is not str
                or set(request) - {"jsonrpc", "id", "method", "params"}):
            return error(None, -32600, "Invalid Request")
        method, params = request["method"], request.get("params", {})
        if "id" not in request:
            if method == "notifications/initialized":
                self.phase = "READY" if self.phase == "INITIALIZING" and params == {} else "INVALIDATED"
            return None
        identifier = request["id"]
        if not (type(identifier) is int and -(2**53 - 1) <= identifier <= 2**53 - 1 or
                type(identifier) is str and 1 <= len(identifier) <= 64 and identifier.isascii()
                and all(32 <= ord(c) < 127 for c in identifier)):
            return error(None, -32600, "Invalid Request")
        if type(params) is not dict:
            return error(identifier, -32602, "Invalid params")
        if method == "ping" and params == {}:
            result = {}
        elif method == "initialize":
            if self.phase != "NEW":
                return error(identifier, -32600, "Already initialized")
            info = params.get("clientInfo")
            if (set(params) != {"protocolVersion", "capabilities", "clientInfo"}
                    or type(params["protocolVersion"]) is not str
                    or len(params["protocolVersion"]) > 32
                    or type(params["capabilities"]) is not dict or type(info) is not dict
                    or any(type(info.get(k)) is not str or not 1 <= len(info[k]) <= 128
                           for k in ("name", "version"))):
                return error(identifier, -32602, "Invalid params")
            self.phase = "INITIALIZING"
            result = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "cgcchild-live-continuity", "version": __version__}}
        elif self.phase != "READY":
            return error(identifier, -32600, "Not initialized")
        elif method == "tools/list":
            if params:
                return error(identifier, -32602, "Invalid params")
            result = {"tools": [self.tool_schema(name) for name in sorted([*TOOLS, STATUS_TOOL])]}
        elif method == "tools/call":
            if set(params) != {"name", "arguments"} or type(params["name"]) is not str:
                return error(identifier, -32602, "Invalid params")
            try:
                value = self.dispatch(params["name"], params["arguments"])
                result = {"content": [{"type": "text", "text": wire(value).decode("ascii").strip()}],
                          "structuredContent": value, "isError": False}
            except (ValueError, OSError, RuntimeError):
                # Never reflect agent payloads, filesystem diagnostics or credentials.
                result = {"content": [{"type": "text", "text": "LIVE_OPERATION_REFUSED"}],
                          "isError": True}
        else:
            return error(identifier, -32601, "Method not found")
        response = wire({"jsonrpc": "2.0", "id": identifier, "result": result})
        return response if len(response) <= MAX_RESPONSE else error(identifier, -32603, "Response limit")

    @staticmethod
    def tool_schema(name):
        is_status = name == STATUS_TOOL
        properties = {} if is_status else {
            "payload": {"type": "object", "description": "Bounded observable engineering facts only; no secrets or private reasoning."},
            "correlation_id": {"type": "string", "minLength": 1, "maxLength": 128},
        }
        return {"name": name, "description": "Read current session summary." if is_status else
                "Append an agent REPORTED claim. Does not verify the claim or authorize project actions.",
                "inputSchema": {"type": "object", "properties": properties,
                                "required": [] if is_status else ["payload"], "additionalProperties": False},
                "annotations": {"readOnlyHint": is_status, "destructiveHint": False,
                                "idempotentHint": is_status, "openWorldHint": False}}


def serve(session, source, destination, *, max_messages=MAX_MESSAGES):
    if type(max_messages) is not int or not 1 <= max_messages <= MAX_MESSAGES:
        raise ValueError("INVALID_MESSAGE_LIMIT")
    adapter = LiveMCPAdapter(session)
    for _ in range(max_messages):
        raw = source.readline(MAX_FRAME + 1)
        if not raw:
            return 0
        result = adapter.handle(raw)
        if result is not None:
            destination.write(result)
            destination.flush()
        if len(raw) > MAX_FRAME or not raw.endswith(b"\n"):
            return 2
    return 0


def launch_codex(session, executable=None):
    """Explicit Windows interactive launch; no shell, prompt or auth configuration.

    The caller is responsible for user invocation. The returned launch observation
    says nothing about Codex task execution or installed plugin interoperability.
    """
    if os.name != "nt":
        raise ValueError("WINDOWS_REQUIRED")
    summary = session.summary()
    if summary["state"] != "RUNNING":
        raise ValueError("SESSION_NOT_RUNNING")
    selected = str(executable) if executable is not None else shutil.which("codex.exe")
    if not selected:
        raise ValueError("CODEX_EXECUTABLE_UNAVAILABLE")
    target = Path(selected).resolve(strict=True)
    if not target.is_file() or target.suffix.lower() != ".exe":
        raise ValueError("CODEX_EXE_REQUIRED")
    env = dict(os.environ)
    env.update(CGC_SESSION_ID=summary["session_id"], CGC_SESSION_DIR=str(session.path),
               CGC_SESSION_GENERATION=str(summary["generation"]), CGC_EVENT_ENDPOINT="stdio")
    process = subprocess.Popen([str(target)], cwd=summary["project_root"], env=env,
                               creationflags=subprocess.CREATE_NEW_CONSOLE, close_fds=True)
    # Launch is explicit and observable, but a report event avoids claiming work success.
    session.report("COMMAND_REPORTED", {"classification": "MANAGED_CODEX_LAUNCH", "pid": process.pid,
                   "status": "PROCESS_CREATED", "task_result": "UNKNOWN"}, actor="CGC launcher")
    return {"pid": process.pid, "state": "PROCESS_CREATED", "task_result": "UNKNOWN",
            "observer_only_available": True, "mutation_authorized": False}
