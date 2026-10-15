"""The key layout and the main loop.

The 13 app keys show apps most-used and most-recent first; a dot marks running
apps. Pressing the key of the app that is already in front cycles its windows.
The two bottom-right keys page up and down; the right-hand display (which has
no buttons) shows the page number.
"""
import logging
import subprocess
import time
from pathlib import Path

from Foundation import NSDate, NSRunLoop
from PIL import Image, ImageDraw, ImageFont

from .apps import app_icon, dock_apps
from .streamdock import KEY_SIZE, SIDE_KEY_SIZE
from .usage import Usage
from .windows import WindowCycler

PREV_KEY, NEXT_KEY = 15, 16  # bottom-right keys
APP_KEYS = [k for k in (r * 6 + c for r in range(3) for c in range(5)) if k not in (PREV_KEY, NEXT_KEY)]
SIDE_KEYS = (5, 11, 17)  # the right-hand display
FONT = "/System/Library/Fonts/SFNS.ttf"
REFRESH_S = 2
KEEP_ALIVE_S = 10
RESORT_S = 300
QUIET_AFTER_PRESS_S = 30  # never reshuffle keys right under the user's finger

log = logging.getLogger("dock-deck")


def app_key(path, running):
    img = Image.new("RGB", (KEY_SIZE, KEY_SIZE), "black")
    icon = app_icon(path).convert("RGBA").resize((84, 84), Image.LANCZOS)
    img.paste(icon, (6, 1), icon)
    if running:
        ImageDraw.Draw(img).ellipse((44, 87, 51, 94), fill="white")
    return img


def text_key(text, active=True, font_size=40, key_size=KEY_SIZE, bg=(30, 30, 30)):
    img = Image.new("RGB", (key_size, key_size), bg)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, font_size)
    d.text((key_size / 2, key_size / 2), text, font=f, anchor="mm", fill="white" if active else (90, 90, 90))
    return img


class DockDeck:
    def __init__(self, deck):
        self.deck = deck
        self.page = 0
        self.apps, self.running = [], set()
        self.shown = {}  # key -> render signature, to only resend changed keys
        self.usage = Usage()
        self.windows = WindowCycler()
        self.last_sort = 0
        self.last_press = 0

    def pages(self):
        return max(1, -(-len(self.apps) // len(APP_KEYS)))

    def refresh(self):
        dock, self.running = dock_apps()
        candidates = dict.fromkeys(dock + [p for p in self.usage.front if Path(p).exists()])
        now = time.monotonic()
        if now - self.last_sort >= RESORT_S and now - self.last_press >= QUIET_AFTER_PRESS_S:
            self.apps = sorted(candidates, key=self.usage.score, reverse=True)
            self.last_sort = now
        else:  # keep the current layout; drop vanished apps, append new ones
            self.apps = [a for a in self.apps if a in candidates] + [a for a in candidates if a not in self.apps]
        self.page = min(self.page, self.pages() - 1)
        self.render()

    def render(self):
        start = self.page * len(APP_KEYS)
        wanted = {}
        for i, key in enumerate(APP_KEYS):
            idx = start + i
            wanted[key] = (self.apps[idx], self.apps[idx] in self.running) if idx < len(self.apps) else None
        many = self.pages() > 1
        wanted[PREV_KEY] = ("▲", many)
        wanted[NEXT_KEY] = ("▼", many)
        for key, text in zip(SIDE_KEYS, ("page", str(self.page + 1), f"of {self.pages()}")):
            wanted[key] = (text, True)

        changed = False
        for key, sig in wanted.items():
            if self.shown.get(key, "unset") == sig:
                continue
            if key in SIDE_KEYS:
                font_size = 48 if key == SIDE_KEYS[1] else 22
                img = text_key(*sig, font_size=font_size, key_size=SIDE_KEY_SIZE, bg="black")
            elif key in (PREV_KEY, NEXT_KEY):
                img = text_key(*sig, font_size=44)
            elif sig is None:
                img = Image.new("RGB", (KEY_SIZE, KEY_SIZE), "black")
            else:
                img = app_key(*sig)
            self.deck.set_image(key, img)
            self.shown[key] = sig
            changed = True
        if changed:
            self.deck.flush()

    def press(self, key):
        self.last_press = time.monotonic()
        if key == PREV_KEY:
            self.page = (self.page - 1) % self.pages()
            self.render()
        elif key == NEXT_KEY:
            self.page = (self.page + 1) % self.pages()
            self.render()
        elif key in APP_KEYS:
            idx = self.page * len(APP_KEYS) + APP_KEYS.index(key)
            if idx < len(self.apps):
                path = self.apps[idx]
                if self.windows.is_front(path) and self.windows.next_window(path):
                    return
                log.info("open %s", path)
                subprocess.Popen(["open", path])

    def run(self):
        self.deck.wake()
        self.deck.clear()
        self.refresh()
        last_refresh = last_alive = time.monotonic()
        while True:
            event = self.deck.read_key(500)
            # let AppKit process workspace notifications, else running/frontmost apps go stale
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.01))
            self.usage.sample()
            if event and event[1]:
                self.press(event[0])
            now = time.monotonic()
            if now - last_refresh >= REFRESH_S:
                self.refresh()
                last_refresh = now
            if now - last_alive >= KEEP_ALIVE_S:
                self.deck.keep_alive()
                last_alive = now
