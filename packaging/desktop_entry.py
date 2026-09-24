"""Frozen entry: normal launch is GUI; explicit arguments select CLI."""
import sys
from cgcchild.cli import main as cli_main
from cgcchild.gui import main as gui_main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise SystemExit(gui_main())
    raise SystemExit(cli_main())
