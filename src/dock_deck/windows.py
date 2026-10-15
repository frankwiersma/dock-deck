"""Cycle through the windows of an app, across all its running instances.

Needs Accessibility permission for the process (System Settings > Privacy &
Security > Accessibility).
"""
import logging

from AppKit import NSWorkspace
from ApplicationServices import (
    AXIsProcessTrustedWithOptions,
    AXUIElementCopyAttributeValue,
    AXUIElementCreateApplication,
    AXUIElementPerformAction,
    AXUIElementSetAttributeValue,
    kAXTrustedCheckOptionPrompt,
)

log = logging.getLogger("dock-deck")


def ensure_trusted():
    """True if we may control windows; otherwise asks macOS to show the grant prompt."""
    return AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})


def _attr(element, name):
    err, value = AXUIElementCopyAttributeValue(element, name, None)
    return value if err == 0 else None


def _instances(path):
    return [
        a
        for a in NSWorkspace.sharedWorkspace().runningApplications()
        if a.bundleURL() and a.bundleURL().path() == path
    ]


def _windows(app):
    """Standard, non-minimized windows of one app instance."""
    element = AXUIElementCreateApplication(app.processIdentifier())
    return [
        (element, w)
        for w in _attr(element, "AXWindows") or []
        if _attr(w, "AXSubrole") == "AXStandardWindow" and not _attr(w, "AXMinimized")
    ]


class WindowCycler:
    def __init__(self):
        self.order = {}  # app path -> windows in rotation order

    def is_front(self, path):
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        return bool(app and app.bundleURL() and app.bundleURL().path() == path)

    def next_window(self, path):
        """Bring the app's next window to the front. Returns False if there is nothing to cycle."""
        current = [pair for app in _instances(path) for pair in _windows(app)]
        if len(current) < 2:
            return False
        known = [p for p in self.order.get(path, []) if p in current]
        rotation = known + [p for p in current if p not in known]
        self.order[path] = rotation

        front = NSWorkspace.sharedWorkspace().frontmostApplication()
        focused = _attr(AXUIElementCreateApplication(front.processIdentifier()), "AXFocusedWindow")
        windows = [w for _, w in rotation]
        i = windows.index(focused) if focused in windows else -1
        app_element, window = rotation[(i + 1) % len(rotation)]

        AXUIElementSetAttributeValue(app_element, "AXFrontmost", True)
        AXUIElementPerformAction(window, "AXRaise")
        AXUIElementSetAttributeValue(window, "AXMain", True)
        log.info("window %d/%d of %s", (i + 1) % len(rotation) + 1, len(rotation), path)
        return True


def close_or_quit(path):
    """Close the app's front window if it has several, else quit the app.

    Returns "closed", "quit", or None when the app isn't running.
    """
    instances = _instances(path)
    if not instances:
        return None
    windows = [w for app in instances for _, w in _windows(app)]
    if len(windows) > 1:
        front = NSWorkspace.sharedWorkspace().frontmostApplication()
        front_pid = front.processIdentifier() if front else None
        for app in sorted(instances, key=lambda a: a.processIdentifier() != front_pid):
            window = _attr(AXUIElementCreateApplication(app.processIdentifier()), "AXFocusedWindow")
            button = window in windows and _attr(window, "AXCloseButton")
            if button:
                AXUIElementPerformAction(button, "AXPress")
                log.info("closed a window of %s", path)
                return "closed"
    for app in instances:
        app.terminate()  # polite quit: the app can still ask to save
    log.info("quit %s", path)
    return "quit"
