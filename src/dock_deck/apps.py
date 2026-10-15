"""The apps to show: what the Dock shows (pinned + running), and their icons."""
from AppKit import (
    NSBitmapImageRep,
    NSDeviceRGBColorSpace,
    NSGraphicsContext,
    NSPNGFileType,
    NSWorkspace,
)
from CoreFoundation import CFPreferencesAppSynchronize, CFPreferencesCopyAppValue
from Foundation import NSURL
from PIL import Image

from .paths import ICON_CACHE

FINDER = "/System/Library/CoreServices/Finder.app"


def dock_apps():
    """Return (pinned + running app paths, set of running app paths)."""
    CFPreferencesAppSynchronize("com.apple.dock")
    pinned = []
    for tile in CFPreferencesCopyAppValue("persistent-apps", "com.apple.dock") or []:
        url = tile.get("tile-data", {}).get("file-data", {}).get("_CFURLString")
        path = url and NSURL.URLWithString_(url).path()
        if path and path.endswith(".app"):
            pinned.append(path.rstrip("/"))
    running = [
        a.bundleURL().path()
        for a in NSWorkspace.sharedWorkspace().runningApplications()
        if a.activationPolicy() == 0 and a.bundleURL()  # 0 = regular app, i.e. shown in the Dock
    ]
    return list(dict.fromkeys([FINDER, *pinned, *running])), set(running) | {FINDER}


def app_icon(path):
    """The app's icon as a 256 px image, rendered once and cached on disk."""
    out = ICON_CACHE / (path.strip("/").replace("/", "_") + ".png")
    if not out.exists():
        ICON_CACHE.mkdir(parents=True, exist_ok=True)
        icon = NSWorkspace.sharedWorkspace().iconForFile_(path)
        rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None, 256, 256, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 0
        )
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.setCurrentContext_(NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep))
        icon.drawInRect_(((0, 0), (256, 256)))
        NSGraphicsContext.restoreGraphicsState()
        rep.representationUsingType_properties_(NSPNGFileType, {}).writeToFile_atomically_(str(out), True)
    return Image.open(out)
