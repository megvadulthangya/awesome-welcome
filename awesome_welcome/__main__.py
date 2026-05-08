#!/usr/bin/env python3
"""Entry point for awesome-welcome."""
import sys
import os

# Ensure the repo root (parent of awesome_welcome/) is on sys.path
# so that 'python awesome_welcome' works after a plain git clone.
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import argparse

from awesome_welcome import config
from awesome_welcome.helpers import has_gui, is_ssh_session


def main():
    parser = argparse.ArgumentParser(description="Manjaro Awesome Respin Welcome")
    parser.add_argument("--test", action="store_true", help="Dry run mode: show commands without executing")
    parser.add_argument("--tui", action="store_true", help="Force TUI mode even if DISPLAY is available")
    parser.add_argument("--services", action="store_true", help="Launch directly into the Service Management view")
    args = parser.parse_args()

    config.DRY_RUN = args.test

    if args.tui:
        from awesome_welcome.tui import run_tui
        run_tui(services_mode=args.services)
    elif has_gui() and not is_ssh_session():
        from awesome_welcome.gui import run_gui
        run_gui(services_mode=args.services)
    else:
        from awesome_welcome.tui import run_tui
        run_tui(services_mode=args.services)


if __name__ == "__main__":
    main()
