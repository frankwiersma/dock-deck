"""App usage ranking: Spotlight launch history plus time each app spends in front.

Spotlight's kMDItemUseCount/kMDItemLastUsedDate only change on launch, so apps
that stay open all day (chat, mail) look unused there. Sampling the
frontmost app fills that gap; the samples persist in usage.json.
"""
import json
import math
import subprocess
import time
from datetime import datetime

from AppKit import NSWorkspace

from .paths import STATE_DIR

STATE = STATE_DIR / "usage.json"
SPOTLIGHT_TTL_S = 300
DAY = 86400


def recency_weight(age_s):
    if age_s < DAY:
        return 4
    if age_s < 7 * DAY:
        return 2
    if age_s < 30 * DAY:
        return 1
    return 0.5


def spotlight(path):
    """(launch count, last used epoch) as recorded by Spotlight."""
    out = subprocess.run(
        ["mdls", "-raw", "-nullMarker", "", "-name", "kMDItemUseCount", "-name", "kMDItemLastUsedDate", path],
        capture_output=True,
        text=True,
    ).stdout.split("\0")  # mdls prints attributes alphabetically: LastUsedDate, UseCount
    try:
        last = datetime.strptime(out[0], "%Y-%m-%d %H:%M:%S %z").timestamp()
    except ValueError:
        last = 0
    count = int(out[1]) if len(out) > 1 and out[1].strip().isdigit() else 0
    return count, last


class Usage:
    def __init__(self):
        try:
            self.front = json.loads(STATE.read_text())  # path -> {"seconds", "last"}
        except (FileNotFoundError, ValueError):
            self.front = {}
        self.spot = {}  # path -> (count, last, fetched_at)
        self.last_sample = time.time()
        self.last_save = self.last_sample

    def sample(self):
        """Credit the time since the previous call to the frontmost app."""
        now = time.time()
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        url = app and app.bundleURL()
        if url:
            entry = self.front.setdefault(url.path(), {"seconds": 0, "last": 0})
            entry["seconds"] += min(now - self.last_sample, 10)
            entry["last"] = now
        self.last_sample = now
        if now - self.last_save > 60:
            STATE.parent.mkdir(parents=True, exist_ok=True)
            STATE.write_text(json.dumps(self.front))
            self.last_save = now

    def score(self, path):
        now = time.time()
        cached = self.spot.get(path)
        if not cached or now - cached[2] > SPOTLIGHT_TTL_S:
            cached = (*spotlight(path), now)
            self.spot[path] = cached
        count, spot_last, _ = cached
        front = self.front.get(path, {"seconds": 0, "last": 0})
        last = max(spot_last, front["last"])
        # log scale: browsers can rack up tens of thousands of "launches" through helper processes
        return math.log1p(count + front["seconds"] / 600) * recency_weight(now - last)
