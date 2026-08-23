#!/usr/bin/env python3
"""
make_mask_previews.py — render PNG previews of the real mask TIFFs for the dashboard.

Browsers cannot display GeoTIFFs, so this script renders the masks to small PNGs
(one per scene, stored next to the source data). The render is a faithful
visualization of the real raster — nothing is synthesized.

Outputs per scene in data/<scene>/:
  * data_mask_preview.png       — usable-data mask: cloud=red, haze/smoke=green,
                                  cloud-shadow=blue, clear=dark, outside scene=black
  * quality_mask_preview.png    — pixel quality mask: per-pixel count of bands that
                                  were interpolated, scaled 0..5+ (nearly black when
                                  the sensor is healthy)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / "data"
MAX_W = 1100  # previews are small — full fidelity isn't needed on a dashboard


def _read_bands_last(path: Path) -> np.ndarray:
    import tifffile

    arr = tifffile.imread(str(path))
    if arr.ndim == 3 and arr.shape[0] in (4, 23, 31) and arr.shape[2] not in (4, 23, 31):
        arr = np.moveaxis(arr, 0, -1)
    return arr


def render_data_mask(path: Path, width: int) -> np.ndarray:
    dm = _read_bands_last(path)
    f = max(1, dm.shape[1] // width)
    dm = dm[::f, ::f, :]
    h, w = dm.shape[:2]

    cloud = (dm[..., 1] == 1)
    haze = (dm[..., 2] == 1)
    shadow = (dm[..., 3] == 1)
    anyd = np.any(dm != 255, axis=-1)

    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    rgb[cloud] = (255, 60, 60)
    rgb[haze] = (80, 230, 80)
    rgb[shadow] = (70, 100, 255)
    # clear pixels: faint dark base so the scene shape is visible
    clear = (dm[..., 0] == 1) & ~cloud & ~haze & ~shadow
    rgb[clear] = (24, 24, 26)
    rgb[~anyd] = (0, 0, 0)
    return rgb


def render_quality_mask(path: Path, width: int) -> np.ndarray:
    pq = _read_bands_last(path)
    f = max(1, pq.shape[1] // width)
    pq = pq[::f, ::f, :]
    h, w = pq.shape[:2]

    interp_per_pixel = (pq == 1).sum(axis=-1).astype(np.float32)  # 0..n_bands
    anyd = np.any(pq != 255, axis=-1)

    # 0 interpolated bands -> black; 5+ -> bright magenta/white
    scaled = np.clip(interp_per_pixel / 5.0, 0, 1)
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    rgb[..., 0] = (255 * scaled).astype(np.uint8)
    rgb[..., 1] = (120 * scaled).astype(np.uint8)
    rgb[..., 2] = (255 * scaled).astype(np.uint8)
    rgb[~anyd] = (0, 0, 0)
    return rgb


def main() -> None:
    scenes = sorted(p for p in DATA.iterdir() if (p / "data_mask.tiff").exists())
    for scene in scenes:
        dm = render_data_mask(scene / "data_mask.tiff", MAX_W)
        pq = render_quality_mask(scene / "pixel_quality_mask.tiff", MAX_W)
        Image.fromarray(dm).save(scene / "data_mask_preview.png")
        Image.fromarray(pq).save(scene / "quality_mask_preview.png")
        print(f"{scene.name}: data_mask_preview.png {dm.shape[1]}x{dm.shape[0]}, "
              f"quality_mask_preview.png {pq.shape[1]}x{pq.shape[0]}")


if __name__ == "__main__":
    main()
