"""Windows-native product entry point. Service is foreground stdio only."""
import argparse
import json
import os
import sys
import time
from . import __version__, sdk
from .core import Workbench, read_input, save_new, security_debt, resource
from .execution import Mode, ACTIONS, plan, DryRunExecutor, SimulationExecutor


def _live_parser(sub):
    live = sub.add_parser("live", help="Explicit project-bound Live Continuity session")
    actions = live.add_subparsers(dest="live_command", required=True)
    start = actions.add_parser("start")
    start.add_argument("--project", required=True)
    start.add_argument("--store")
    start.add_argument("--worker-type", default="Codex")
    start.add_argument("--worker-version")
    actions.add_parser("list").add_argument("--store")
    actions.add_parser("open").add_argument("--input", required=True)
    for name in ("status", "observe", "report", "test", "checkpoint", "preserve", "end",
                 "interrupt", "recover", "resume", "serve", "watch", "launch"):
        command = actions.add_parser(name)
        command.add_argument("--session", required=name != "serve")
        if name == "observe":
            command.add_argument("--verify-remote", action="store_true")
        elif name == "report":
            command.add_argument("--event-type", required=True)
            command.add_argument("--payload", required=True, help="Bounded JSON object; no secrets or private reasoning")
            command.add_argument("--correlation-id")
        elif name == "test":
            command.add_argument("--framework", choices=("unittest", "pytest", "npm"), default="unittest")
            command.add_argument("--timeout", type=float, default=60, help="Finite command timeout, greater than 0 and at most 600 seconds")
            command.add_argument("test_command", nargs=argparse.REMAINDER)
        elif name == "interrupt":
            command.add_argument("--reason", default="USER_INTERRUPTED")
        elif name == "serve":
            command.add_argument("--max-messages", type=int, default=4096)
        elif name == "watch":
            command.add_argument("--duration", type=int, required=True, help="Finite foreground duration, 1..3600 seconds")
            command.add_argument("--interval", type=float, default=2)
            command.add_argument("--checkpoint-interval", type=int, default=300)
        elif name == "launch":
            command.add_argument("--executable", help="Explicit native Codex .exe; default codex.exe on PATH")


def _live_main(args):
    from .live import Session, default_store, discover_sessions, open_capsule
    from .live.adapter import serve, launch_codex, decode_request, MAX_FRAME
    command = args.live_command
    if command == "start":
        session = Session.start(args.project, store=args.store, worker_type=args.worker_type,
                                worker_version=args.worker_version)
        result = {**session.summary(), "storage_location": str(session.path)}
    elif command == "list":
        result = {"sessions": discover_sessions(args.store),
                  "store": str(args.store or default_store()), "mutation_authorized": False}
    elif command == "open":
        result = open_capsule(args.input)
    else:
        selected = args.session or os.environ.get("CGC_SESSION_DIR")
        if not selected:
            raise ValueError("SESSION_REQUIRED")
        session = Session.open(selected)
        if command == "serve":
            return serve(session, sys.stdin.buffer, sys.stdout.buffer, max_messages=args.max_messages)
        if command == "status":
            result = {**session.summary(), "storage_location": str(session.path)}
        elif command == "observe":
            result = session.observe(verify_remote=args.verify_remote)
        elif command == "report":
            if len(args.payload) > MAX_FRAME:
                raise ValueError("PAYLOAD_LIMIT")
            payload = decode_request((args.payload + "\n").encode("utf-8"))
            if type(payload) is not dict:
                raise ValueError("INVALID_PAYLOAD")
            result = session.report(args.event_type, payload, correlation_id=args.correlation_id)
        elif command == "test":
            test_command = args.test_command
            if test_command[:1] == ["--"]:
                test_command = test_command[1:]
            if not test_command:
                raise ValueError("TEST_COMMAND_REQUIRED")
            if not 0 < args.timeout <= 600:
                raise ValueError("INVALID_TEST_TIMEOUT")
            result = session.run_test(test_command, framework=args.framework, timeout=args.timeout)
        elif command == "checkpoint":
            result = session.checkpoint()
        elif command in ("preserve", "end"):
            result = {"capsule": str(session.preserve()), "mutation_authorized": False}
        elif command == "interrupt":
            session.interrupt(args.reason)
            result = session.summary()
        elif command == "recover":
            result = session.recover()
        elif command == "resume":
            session.resume()
            result = session.summary()
        elif command == "launch":
            result = launch_codex(session, args.executable)
        elif command == "watch":
            if not (1 <= args.duration <= 3600 and 0.1 <= args.interval <= 60
                    and 1 <= args.checkpoint_interval <= 3600):
                raise ValueError("INVALID_WATCH_LIMIT")
            deadline = time.monotonic() + args.duration
            next_checkpoint = time.monotonic() + args.checkpoint_interval
            observations = 0
            try:
                while time.monotonic() < deadline:
                    session.observe()
                    observations += 1
                    if time.monotonic() >= next_checkpoint:
                        session.checkpoint()
                        next_checkpoint = time.monotonic() + args.checkpoint_interval
                    time.sleep(min(args.interval, max(0, deadline - time.monotonic())))
                session.checkpoint()
            except KeyboardInterrupt:
                session.interrupt("FOREGROUND_WATCH_INTERRUPTED")
                return 130
            result = {"state": "WATCH_FINISHED", "observations": observations,
                      "session": session.summary(), "mutation_authorized": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    if command == "test":
        state = result.get("verification_state", "UNKNOWN")
        if state == "VERIFIED_PASS":
            return 0
        if state in ("VERIFIED_FAIL", "CONTRADICTED", "COMMAND_FAILED_TEST_COUNTS_UNKNOWN"):
            return 1
        # Process success without parsed results is not verified test success.
        return 2
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cgcchild", description="CREDID GUARDIAN CODEX experimental workbench")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--mode", choices=[m.value for m in Mode], default=Mode.READ_ONLY_SAFE.value)
    sub = parser.add_subparsers(dest="command", required=True)
    _live_parser(sub)
    for name in ("status", "inspect", "review", "reconcile", "safe-resume", "report", "capsule-export", "capsule-import", "serve"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--input", required=name != "status")
        if name in ("report", "capsule-export", "capsule-import"):
            cmd.add_argument("--output", required=True)
    sub.add_parser("debt")
    sub.add_parser("self-test")
    sample = sub.add_parser("example")
    sample.add_argument("--output", required=True)
    for name in ("plan", "dry-run", "simulate"):
        sub.add_parser(name).add_argument("action", choices=ACTIONS)
    sub.add_parser("gui").add_argument("--smoke-output", help="Write a GUI smoke PNG to a new file and exit")
    args = parser.parse_args(argv)
    try:
        if args.command == "live":
            return _live_main(args)
        mode = Mode(args.mode)
        app = Workbench(mode)
        if getattr(args, "input", None):
            app.load(read_input(args.input))
        cmd = args.command
        if cmd == "gui":
            from .gui import main as gui_main
            return gui_main(mode=mode, smoke_output=args.smoke_output)
        if cmd == "serve":
            from cgc.experimental.mcp_stdio import serve
            return serve(sdk.encode(app.snapshot()), sys.stdin.buffer, sys.stdout.buffer)
        if cmd == "debt": result = security_debt()
        elif cmd == "plan": result = plan(args.action, mode)
        elif cmd == "dry-run": result = DryRunExecutor().execute(args.action, mode)
        elif cmd == "simulate": result = SimulationExecutor().execute(args.action, mode)
        elif cmd == "self-test":
            value = sdk.decode(resource("example.json"))
            assert sdk.import_capsule(sdk.export_capsule(value)) == value
            assert len(security_debt()) >= 6
            result = dict(state="PASSED", checks=["RESOURCES", "SCHEMA", "CAPSULE_ROUNDTRIP", "SECURITY_DEBT"], mutation_authorized=False)
        elif cmd == "example":
            save_new(args.output, resource("example.json"))
            result = {"state": "EXPORTED_SYNTHETIC_EXAMPLE"}
        elif cmd in ("review", "reconcile", "safe-resume"): result = app.review()
        elif cmd in ("report", "capsule-export", "capsule-import"):
            value = app.snapshot()
            raw = sdk.report(value) if cmd == "report" else sdk.export_capsule(value) if cmd == "capsule-export" else sdk.encode(value)
            save_new(args.output, raw)
            result = {"state": "EXPORTED", "mutation_authorized": False}
        else: result = app.status()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if isinstance(result, dict) and result.get("state") == "REFUSED" else 0
    except (ValueError, OSError, RuntimeError) as error:
        # Fixed errors only; no selected document, path or OS diagnostic echo.
        code = str(error) if type(error) is ValueError and str(error).replace("_", "").isalnum() else "OPERATION_REFUSED"
        print(json.dumps({"error": code, "mutation_authorized": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
