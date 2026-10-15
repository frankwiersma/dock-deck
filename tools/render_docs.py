"""Render the README images (docs/deck.png, docs/demo.gif) with generic, original icons.

Run: .venv/bin/python tools/render_docs.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "docs"
FONT = "/System/Library/Fonts/SFNS.ttf"
S = 2  # supersampling
KEY = 95 * S
SIDE = 82 * S
GAP = 22 * S
PAD = 40 * S
RADIUS = 14 * S


def font(size):
    return ImageFont.truetype(FONT, size * S)


# --- generic icons: a coloured tile with a simple white glyph --------------------------


def _tile(top, bottom):
    size = 84 * S
    grad = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / (size - 1)
        grad.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    img = grad.resize((size, size)).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=19 * S, fill=255)
    img.putalpha(mask)
    return img


def _globe(d, c):
    d.ellipse((c - 26 * S, c - 26 * S, c + 26 * S, c + 26 * S), outline="white", width=4 * S)
    d.ellipse((c - 11 * S, c - 26 * S, c + 11 * S, c + 26 * S), outline="white", width=3 * S)
    d.line((c - 26 * S, c, c + 26 * S, c), fill="white", width=3 * S)


def _mail(d, c):
    d.rounded_rectangle((c - 28 * S, c - 19 * S, c + 28 * S, c + 19 * S), radius=4 * S, outline="white", width=4 * S)
    d.line((c - 26 * S, c - 16 * S, c, c + 4 * S, c + 26 * S, c - 16 * S), fill="white", width=4 * S, joint="curve")


def _chat(d, c):
    d.rounded_rectangle((c - 28 * S, c - 22 * S, c + 28 * S, c + 14 * S), radius=14 * S, fill="white")
    d.polygon(((c - 16 * S, c + 10 * S), (c - 22 * S, c + 26 * S), (c - 2 * S, c + 12 * S)), fill="white")


def _calendar(d, c):
    d.rounded_rectangle((c - 27 * S, c - 24 * S, c + 27 * S, c + 26 * S), radius=6 * S, fill="white")
    d.rectangle((c - 27 * S, c - 24 * S, c + 27 * S, c - 10 * S), fill=(235, 70, 70))
    for i in range(3):
        for j in range(4):
            x, y = c - 18 * S + j * 12 * S, c - 1 * S + i * 9 * S
            d.ellipse((x - 2 * S, y - 2 * S, x + 2 * S, y + 2 * S), fill=(120, 120, 120))


def _music(d, c):
    d.ellipse((c - 22 * S, c + 8 * S, c - 4 * S, c + 22 * S), fill="white")
    d.ellipse((c + 6 * S, c + 2 * S, c + 24 * S, c + 16 * S), fill="white")
    d.line((c - 6 * S, c + 14 * S, c - 6 * S, c - 22 * S), fill="white", width=4 * S)
    d.line((c + 22 * S, c + 8 * S, c + 22 * S, c - 28 * S), fill="white", width=4 * S)
    d.polygon(((c - 8 * S, c - 22 * S), (c + 24 * S, c - 30 * S), (c + 24 * S, c - 20 * S), (c - 8 * S, c - 12 * S)), fill="white")


def _text(label, size):
    def draw(d, c):
        d.text((c, c), label, font=font(size), anchor="mm", fill="white")

    return draw


def _notes(d, c):
    d.rounded_rectangle((c - 24 * S, c - 28 * S, c + 24 * S, c + 28 * S), radius=5 * S, fill="white")
    for i in range(4):
        y = c - 14 * S + i * 11 * S
        d.line((c - 14 * S, y, c + 14 * S, y), fill=(200, 160, 40), width=3 * S)


def _photos(d, c):
    d.ellipse((c + 6 * S, c - 22 * S, c + 20 * S, c - 8 * S), fill="white")
    d.polygon(((c - 28 * S, c + 22 * S), (c - 8 * S, c - 10 * S), (c + 6 * S, c + 10 * S), (c + 14 * S, c), (c + 28 * S, c + 22 * S)), fill="white")


def _folder(d, c):
    d.rounded_rectangle((c - 28 * S, c - 20 * S, c - 2 * S, c - 8 * S), radius=4 * S, fill="white")
    d.rounded_rectangle((c - 28 * S, c - 14 * S, c + 28 * S, c + 22 * S), radius=5 * S, fill="white")


def _gear(d, c):
    for k in range(8):
        a = k * math.pi / 4
        dx, dy = math.cos(a), math.sin(a)
        d.line((c + dx * 14 * S, c + dy * 14 * S, c + dx * 28 * S, c + dy * 28 * S), fill="white", width=10 * S)
    d.ellipse((c - 21 * S, c - 21 * S, c + 21 * S, c + 21 * S), fill="white")
    d.ellipse((c - 9 * S, c - 9 * S, c + 9 * S, c + 9 * S), fill=(110, 110, 120))


def _camera(d, c):
    d.rounded_rectangle((c - 28 * S, c - 16 * S, c + 28 * S, c + 22 * S), radius=7 * S, fill="white")
    d.rectangle((c - 10 * S, c - 24 * S, c + 10 * S, c - 14 * S), fill="white")
    d.ellipse((c - 12 * S, c - 9 * S, c + 12 * S, c + 15 * S), fill=(60, 60, 70))


def _pin(d, c):
    d.ellipse((c - 18 * S, c - 28 * S, c + 18 * S, c + 8 * S), fill="white")
    d.polygon(((c - 15 * S, c), (c + 15 * S, c), (c, c + 28 * S)), fill="white")
    d.ellipse((c - 7 * S, c - 17 * S, c + 7 * S, c - 3 * S), fill=(40, 160, 90))


def _play(d, c):
    d.polygon(((c - 14 * S, c - 22 * S), (c - 14 * S, c + 22 * S), (c + 22 * S, c)), fill="white")


def _grid(d, c):
    d.rounded_rectangle((c - 26 * S, c - 24 * S, c + 26 * S, c + 24 * S), radius=4 * S, outline="white", width=4 * S)
    for k in (-8, 8):
        d.line((c - 26 * S, c + k * S, c + 26 * S, c + k * S), fill="white", width=3 * S)
    d.line((c - 8 * S, c - 24 * S, c - 8 * S, c + 24 * S), fill="white", width=3 * S)


def _bars(d, c):
    for i, h in enumerate((18, 34, 26, 44)):
        x = c - 26 * S + i * 14 * S
        d.rounded_rectangle((x, c + 24 * S - h * S, x + 9 * S, c + 24 * S), radius=2 * S, fill="white")


def _sun(d, c):
    for k in range(8):
        a = k * math.pi / 4
        d.line((c + math.cos(a) * 18 * S, c + math.sin(a) * 18 * S, c + math.cos(a) * 28 * S, c + math.sin(a) * 28 * S), fill="white", width=4 * S)
    d.ellipse((c - 13 * S, c - 13 * S, c + 13 * S, c + 13 * S), fill="white")


def _shapes(d, c):
    d.ellipse((c - 26 * S, c - 26 * S, c - 2 * S, c - 2 * S), fill="white")
    d.rectangle((c + 4 * S, c - 24 * S, c + 24 * S, c - 4 * S), fill="white")
    d.polygon(((c - 14 * S, c + 4 * S), (c - 26 * S, c + 26 * S), (c - 2 * S, c + 26 * S)), fill="white")
    d.ellipse((c + 2 * S, c + 2 * S, c + 26 * S, c + 26 * S), outline="white", width=4 * S)


ICONS = [  # (top colour, bottom colour, glyph, running?)
    ((80, 160, 255), (30, 90, 220), _globe, True),
    ((90, 200, 255), (20, 120, 230), _mail, True),
    ((110, 220, 120), (30, 160, 70), _chat, True),
    ((250, 250, 250), (225, 225, 230), _calendar, True),
    ((255, 100, 130), (220, 30, 80), _music, True),
    ((70, 70, 80), (20, 20, 25), _text(">_", 30), True),
    ((60, 140, 230), (25, 70, 170), _text("</>", 26), True),
    ((255, 215, 90), (240, 170, 30), _notes, False),
    ((255, 170, 90), (235, 90, 120), _photos, False),
    ((110, 190, 255), (60, 130, 230), _folder, True),
    ((160, 160, 170), (100, 100, 110), _gear, False),
    ((90, 90, 100), (40, 40, 50), _camera, False),
    ((120, 220, 150), (40, 160, 90), _pin, False),
    ((255, 90, 90), (200, 30, 40), _play, True),
    ((60, 190, 110), (20, 130, 70), _grid, False),
    ((80, 140, 250), (40, 80, 200), _text("Aa", 28), False),
    ((255, 160, 60), (230, 100, 30), _bars, False),
    ((100, 190, 255), (255, 200, 80), _sun, False),
    ((180, 110, 255), (110, 50, 220), _shapes, False),
]


def icon_key(spec):
    top, bottom, glyph, running = spec
    key = Image.new("RGBA", (KEY, KEY), (0, 0, 0, 255))
    tile = _tile(top, bottom)
    glyph(ImageDraw.Draw(tile), tile.width // 2)
    key.alpha_composite(tile, (6 * S, 1 * S))
    if running:
        ImageDraw.Draw(key).ellipse((44 * S, 87 * S, 51 * S, 94 * S), fill="white")
    return key


def text_key(label, size, bg=(30, 30, 30), w=KEY):
    key = Image.new("RGBA", (w, w), bg + (255,))
    ImageDraw.Draw(key).text((w / 2, w / 2), label, font=font(size), anchor="mm", fill="white")
    return key


# --- the device ----------------------------------------------------------------------------


def device(page, pages, apps, pressed=None, caption=None):
    grid_w = 5 * KEY + 4 * GAP
    grid_h = 3 * KEY + 2 * GAP
    w = PAD + grid_w + GAP + SIDE + PAD
    h = PAD + grid_h + PAD
    cap_h = 64 * S if caption is not None else 0
    img = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD + cap_h), (0, 0, 0, 0))

    body = (PAD, PAD, PAD + w, PAD + h)
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(tuple(v + (12 * S if i % 2 else 0) for i, v in enumerate(body)), radius=36 * S, fill=(0, 0, 0, 110))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18 * S)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(body, radius=36 * S, fill=(38, 39, 44), outline=(70, 72, 80), width=2 * S)

    ox, oy = PAD + PAD, PAD + PAD
    keys = {}
    for i, spec in enumerate(apps):
        keys[[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14][i]] = icon_key(spec)
    keys[15] = text_key("▲", 44)
    keys[16] = text_key("▼", 44)
    for pos in range(18):
        r, c = divmod(pos, 6)
        if c == 5:
            continue
        x, y = ox + c * (KEY + GAP), oy + r * (KEY + GAP)
        k = keys.get(pos, Image.new("RGBA", (KEY, KEY), (0, 0, 0, 255)))
        mask = Image.new("L", (KEY, KEY), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, KEY - 1, KEY - 1), radius=RADIUS, fill=255)
        frame = Image.new("RGBA", (KEY, KEY), (0, 0, 0, 0))
        frame.paste(k, (0, 0), mask)
        if pos == pressed:
            glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(glow).rounded_rectangle((x - 6 * S, y - 6 * S, x + KEY + 6 * S, y + KEY + 6 * S), radius=RADIUS + 6 * S, fill=(120, 190, 255, 220))
            img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(7 * S)))
        img.alpha_composite(frame, (x, y))
        d.rounded_rectangle((x, y, x + KEY, y + KEY), radius=RADIUS, outline=(20, 20, 22), width=2 * S)
        if pos == pressed:
            d.rounded_rectangle((x - 4 * S, y - 4 * S, x + KEY + 4 * S, y + KEY + 4 * S), radius=RADIUS + 4 * S, outline=(120, 190, 255), width=4 * S)

    # right-hand display: one screen, no buttons
    sx = ox + 5 * (KEY + GAP)
    sy0, sy1 = oy, oy + grid_h
    d.rounded_rectangle((sx, sy0, sx + SIDE, sy1), radius=RADIUS, fill=(0, 0, 0), outline=(20, 20, 22), width=2 * S)
    mid = sx + SIDE / 2
    d.text((mid, sy0 + KEY / 2), "page", font=font(22), anchor="mm", fill="white")
    d.text((mid, (sy0 + sy1) / 2), str(page), font=font(48), anchor="mm", fill="white")
    d.text((mid, sy1 - KEY / 2), f"of {pages}", font=font(22), anchor="mm", fill="white")

    if caption is not None:
        d.text((img.width / 2, h + 2 * PAD + cap_h / 2 - 8 * S), caption, font=font(24), anchor="mm", fill=(140, 140, 150))
    return img


def flat(img, bg):
    out = Image.new("RGB", img.size, bg)
    out.paste(img, (0, 0), img)
    return out


def main():
    OUT.mkdir(exist_ok=True)
    page1, page2 = ICONS[:13], ICONS[13:]

    hero = device(1, 2, page1)
    hero.resize((hero.width // S, hero.height // S), Image.LANCZOS).save(OUT / "deck.png")

    bg = (246, 247, 249)
    steps = [
        (1, page1, None, "13 apps per page, most used first"),
        (1, page1, 16, "press ▼ for the next page"),
        (2, page2, None, "page 2"),
        (2, page2, 15, "press ▲ to go back"),
        (1, page1, None, "13 apps per page, most used first"),
        (1, page1, 0, "press an app to open it, again to cycle its windows"),
    ]
    frames, durations = [], []
    for page, apps, pressed, caption in steps:
        f = flat(device(page, 2, apps, pressed, caption), bg)
        frames.append(f.resize((f.width // S, f.height // S), Image.LANCZOS))
        durations.append(700 if pressed is not None else 1600)
    frames[0].save(OUT / "demo.gif", save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print("wrote", OUT / "deck.png", OUT / "demo.gif")


if __name__ == "__main__":
    main()
