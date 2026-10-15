"""Command line: run the deck, or (un)install the login agent."""
import argparse
import logging
import os
import plistlib
import subprocess
import sys
import time

from . import __version__
from .deck import DockDeck
from .paths import AGENT_LABEL, AGENT_PLIST, LOG_FILE
from .streamdock import StreamDock
from .windows import ensure_trusted

log = logging.getLogger("dock-deck")


def run():
    if not ensure_trusted():
        log.warning("no Accessibility permission: window cycling is off until it is granted")
    while True:
        try:
            deck = StreamDock()
        except OSError as e:
            log.info("%s; retrying", e)
            time.sleep(5)
            continue
        try:
            DockDeck(deck).run()
        except OSError as e:
            log.warning("device error: %s; reconnecting", e)
        finally:
            deck.close()
        time.sleep(2)


def _bootout():
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{AGENT_LABEL}"], capture_output=True)


def install_agent():
    exe = sys.argv[0]  # the installed dock-deck entry point
    AGENT_PLIST.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with AGENT_PLIST.open("wb") as f:
        plistlib.dump(
            {
                "Label": AGENT_LABEL,
                "ProgramArguments": [os.path.abspath(exe)],
                "RunAtLoad": True,
                "KeepAlive": True,
                "ThrottleInterval": 10,
                "ProcessType": "Interactive",
                "StandardOutPath": str(LOG_FILE),
                "StandardErrorPath": str(LOG_FILE),
            },
            f,
        )
    _bootout()
    subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(AGENT_PLIST)], check=True)
    print(f"dock-deck now starts at login (logs: {LOG_FILE})")


def uninstall_agent():
    _bootout()
    AGENT_PLIST.unlink(missing_ok=True)
    print("login agent removed")


def main():
    parser = argparse.ArgumentParser(prog="dock-deck", description="Your Mac's Dock on a Mirabox/Ajazz-style stream dock.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "install-agent", "uninstall-agent"])
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    {"run": run, "install-agent": install_agent, "uninstall-agent": uninstall_agent}[args.command]()
