#!/usr/bin/env python3
"""
make_web_images.py — make small web copies of each scene's preview and thumbnail.

The delivered preview.png files are 7-20 MB, far too heavy for a web page. The dashboard
loads these smaller JPEGs instead; the full-size originals stay in data/ untouched.

    preview.png   -> preview_web.jpg    (max 1600 px wide)
    thumbnail.png -> thumbnail_web.jpg  (max 640 px wide)

Usage:
    .venv/bin/python dashboard/make_web_images.py
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # these are trusted local files

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [("preview.png", "preview_web.jpg", 1600, 82), ("thumbnail.png", "thumbnail_web.jpg", 640, 80)]


def shrink(src: Path, dst: Path, max_w: int, quality: int) -> None:
    with Image.open(src) as im:
        im = im.convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)


def main() -> None:
    folders = [s["folder"] for s in json.loads((ROOT / "agent" / "decisions.json").read_text())["scenes"]]
    for folder in folders:
        for src_name, dst_name, max_w, quality in TARGETS:
            src, dst = ROOT / "data" / folder / src_name, ROOT / "data" / folder / dst_name
            shrink(src, dst, max_w, quality)
            print(f"{folder}/{dst_name}: {src.stat().st_size / 1048576:.1f} MB -> {dst.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
