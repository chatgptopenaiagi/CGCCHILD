"""Windows-native product entry point. Service is foreground stdio only."""
import argparse
import json
import sys
from . import __version__, sdk
from .core import Workbench, read_input, save_new, security_debt, resource
from .execution import Mode, ACTIONS, plan, DryRunExecutor, SimulationExecutor


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cgcchild", description="CREDID GUARDIAN CODEX experimental workbench")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--mode", choices=[m.value for m in Mode], default=Mode.READ_ONLY_SAFE.value)
    sub = parser.add_subparsers(dest="command", required=True)
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
