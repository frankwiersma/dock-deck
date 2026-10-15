"""Where dock-deck keeps its state, cache and logs (standard macOS locations)."""
from pathlib import Path

HOME = Path.home()
STATE_DIR = HOME / "Library" / "Application Support" / "dock-deck"
ICON_CACHE = HOME / "Library" / "Caches" / "dock-deck" / "icons"
LOG_FILE = HOME / "Library" / "Logs" / "dock-deck.log"
AGENT_LABEL = "io.github.dock-deck"
AGENT_PLIST = HOME / "Library" / "LaunchAgents" / f"{AGENT_LABEL}.plist"
