#!/usr/bin/env python3
"""
make_images.py — generate the walkthrough visuals from real scene artifacts.

For each scene in data/ this produces, into docs/images/:
  * <folder>_preview.png  — L2A RGB composite (downsampled copy of the delivered preview)
  * <folder>_mask.png     — rendered usable-data mask: cloud=red, haze=green,
                            cloud-shadow=blue, clear=transparent dark (from data_mask.tiff)
  * <folder>_overlay.png  — preview dimmed with the mask painted on top

Nothing here is synthesized: every pixel comes from the delivered TIFF/PNG.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / "data"
OUT = ROOT / "images"
MAX_W = 1400


def load_mask_rgb(path: Path, width: int) -> np.ndarray:
    import tifffile

    dm = tifffile.imread(str(path))
    if dm.ndim == 3 and dm.shape[0] == 4:
        dm = np.moveaxis(dm, 0, -1)          # (B,H,W) -> (H,W,B)
    h, w = dm.shape[:2]
    f = max(1, w // width)
    dm = dm[::f, ::f, :]

    cloud = (dm[..., 1] == 1).astype(np.float32)
    haze = (dm[..., 2] == 1).astype(np.float32)
    shadow = (dm[..., 3] == 1).astype(np.float32)
    clear = (dm[..., 0] == 1).astype(np.float32)
    anyd = (np.any(dm != 255, axis=-1)).astype(np.float32)

    rgb = np.zeros((*cloud.shape, 3), dtype=np.float32)
    rgb[..., 0] = cloud * 255
    rgb[..., 1] = haze * 255
    rgb[..., 2] = shadow * 255
    # dim the clear pixels to a near-black base so obstructions pop
    base = np.clip(clear[..., None] * 14, 0, 255).astype(np.float32)
    rgb = np.maximum(rgb, base)
    rgb[anyd < 0.5] = 0                       # outside footprint
    return rgb


def load_resized(path: Path, width: int) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    scenes = sorted(p for p in DATA.iterdir() if (p / "stac_metadata.json").exists())
    for scene in scenes:
        preview_png = scene / "preview.png"
        mask_tiff = scene / "data_mask.tiff"
        if not preview_png.exists() or not mask_tiff.exists():
            print(f"skip {scene.name}: missing preview or mask")
            continue

        mask_rgb = load_mask_rgb(mask_tiff, MAX_W)
        preview = load_resized(preview_png, mask_rgb.shape[1])
        # align preview height to mask height (masks are taller than previews usually)
        if preview.shape[0] > mask_rgb.shape[0]:
            preview = preview[: mask_rgb.shape[0]]
        elif preview.shape[0] < mask_rgb.shape[0]:
            mask_rgb = mask_rgb[: preview.shape[0]]

        overlay = np.clip(preview * 0.45 + mask_rgb * 0.85, 0, 255).astype(np.uint8)
        preview_u8 = np.clip(preview, 0, 255).astype(np.uint8)
        mask_u8 = mask_rgb.astype(np.uint8)

        for name, arr in (("preview", preview_u8), ("mask", mask_u8), ("overlay", overlay)):
            Image.fromarray(arr).save(OUT / f"{scene.name}_{name}.png")
        print(f"{scene.name}: wrote preview/mask/overlay "
              f"({preview_u8.shape[1]}x{preview_u8.shape[0]})")


if __name__ == "__main__":
    main()
