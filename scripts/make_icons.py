#!/usr/bin/env python3
"""Generate the header logo, favicons and home-screen icons from one source image.

Usage:
    python scripts/make_icons.py path/to/logo.png

Writes into assets/:
    logo.png              header logo, 160 px tall, transparent background
    favicon-32.png        browser tab icon
    favicon-48.png        browser tab icon (high-DPI)
    apple-touch-icon.png  180 x 180, opaque background (iOS ignores transparency)
    icon-192.png          Android / manifest icon
    icon-512.png          Android / manifest icon
    icon-maskable-512.png manifest maskable icon (content inside the 80 % safe zone)

Requires Pillow:  pip install pillow
"""
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install pillow")

BG_LIGHT = (246, 248, 250, 255)   # snow white used for opaque icons
OUT = Path(__file__).resolve().parent.parent / "assets"


def fit(im: Image.Image, size: int, content_ratio: float = 1.0, bg=None) -> Image.Image:
    """Return a size x size image with `im` scaled to `content_ratio` of the box and centred."""
    canvas = Image.new("RGBA", (size, size), bg or (0, 0, 0, 0))
    box = int(size * content_ratio)
    scaled = im.copy()
    scaled.thumbnail((box, box), Image.LANCZOS)
    x = (size - scaled.width) // 2
    y = (size - scaled.height) // 2
    canvas.alpha_composite(scaled, (x, y))
    return canvas


def main(src_path: str) -> None:
    src = Image.open(src_path).convert("RGBA")
    # Trim fully transparent margins so the mark fills its box.
    bbox = src.getchannel("A").getbbox()
    if bbox:
        src = src.crop(bbox)
    OUT.mkdir(parents=True, exist_ok=True)

    # Header logo: 160 px tall (rendered at 40 / 32 px, so crisp on 3x and 4x screens).
    logo = src.copy()
    logo.thumbnail((10_000, 160), Image.LANCZOS)
    logo.save(OUT / "logo.png", optimize=True)

    fit(src, 32, 1.0).save(OUT / "favicon-32.png", optimize=True)
    fit(src, 48, 1.0).save(OUT / "favicon-48.png", optimize=True)
    fit(src, 180, 0.86, BG_LIGHT).convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
    fit(src, 192, 1.0).save(OUT / "icon-192.png", optimize=True)
    fit(src, 512, 1.0).save(OUT / "icon-512.png", optimize=True)
    fit(src, 512, 0.72, BG_LIGHT).save(OUT / "icon-maskable-512.png", optimize=True)

    for p in sorted(OUT.glob("*.png")):
        print(f"{p.name:24s} {p.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
