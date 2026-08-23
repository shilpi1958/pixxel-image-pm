"""
analyze_scene.py — reduce a scene's delivered artifacts to QA metrics.

Reads, for one scene:
  * stac_metadata.json      — catalog record (platform, level, cloud cover, …)
  * data_mask.tiff          — 4-band usable-data mask (clear/cloud/haze/cloud-shadow)
  * pixel_quality_mask.tiff — per-band quality flags (0 ok, 1 interpolated, 255 NoData)
  * optional band stack (COG) — full spectral data, needed for QA-6/QA-7

Mask semantics (Wyvern Data Product Guide, "Usable Data Mask" / "Pixel Quality Mask"):
  Data mask bands (1=present, 0=absent, 255=NoData): 1 clear, 2 cloud, 3 haze, 4 cloud-shadow.
  Pixel quality mask: per band, 0 = no documented condition, 1 = interpolated pixel, 255 = NoData.

The COG is uint16 with raster scale 0.0001 (reflectance = DN * 0.0001) and nodata 65535.
It is optional here: this repo deliberately does not mirror the 2-3 GB per-scene COGs
(see data/README.md), so QA-6/QA-7 metrics are reported as None (not assessable) unless
a band stack is supplied with --cog.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import tifffile

MASK_BAND_NAMES = ["clear", "cloud", "haze", "cloud_shadow"]


def _read_bands_last(path: Path) -> np.ndarray:
    """Read a mask tiff, normalizing to (H, W, B) regardless of stored layout."""
    arr = tifffile.imread(str(path))
    if arr.ndim == 3 and arr.shape[0] in (4, 23, 31) and arr.shape[2] not in (4, 23, 31):
        # bands-first layout (H,W) -> (B,H,W); transpose to (H,W,B)
        arr = np.moveaxis(arr, 0, -1)
    return arr


def load_stac_metadata(path: Path) -> dict:
    with open(path) as f:
        item = json.load(f)
    props = item["properties"]
    bands = item["assets"].get("Cloud optimized GeoTiff", {}).get("eo:bands", [])
    cog_meta = item["assets"].get("Cloud optimized GeoTiff", {})
    raster_bands = cog_meta.get("raster:bands", [])
    return {
        "scene_id": item["id"],
        "collection": item.get("collection"),
        "datetime": props.get("datetime"),
        "start_datetime": props.get("start_datetime"),
        "end_datetime": props.get("end_datetime"),
        "platform": props.get("platform"),
        "processing_level": props.get("processing:level"),
        "processing_version": props.get("processing:version"),
        "stac_cloud_cover_pct": props.get("eo:cloud_cover"),
        "gsd_m": props.get("gsd"),
        "proj_epsg": props.get("proj:epsg"),
        "proj_shape": props.get("proj:shape"),
        "view_off_nadir": props.get("view:off_nadir"),
        "view_sun_elevation": props.get("view:sun_elevation"),
        "bbox": item.get("bbox"),
        "eo_bands": bands,
        "cog_href": cog_meta.get("href"),
        "cog_scale": raster_bands[0].get("scale") if raster_bands else None,
        "cog_nodata": raster_bands[0].get("nodata") if raster_bands else None,
    }


def analyze_masks(data_mask_path: Path, pq_mask_path: Path) -> dict:
    """Reduce both masks to per-scene metrics over the valid data footprint."""
    dm = _read_bands_last(data_mask_path)
    if dm.ndim != 3 or dm.shape[2] != 4:
        raise ValueError(f"data mask {data_mask_path} has unexpected shape {dm.shape}")

    pq = _read_bands_last(pq_mask_path)
    if pq.ndim != 3:
        raise ValueError(f"pixel quality mask {pq_mask_path} has unexpected shape {pq.shape}")

    valid = np.any(dm != 255, axis=-1)          # data footprint (scene area)
    vtot = max(int(valid.sum()), 1)
    n_bands = pq.shape[2]
    total_pixels = valid.size

    cloud = (dm[..., 1] == 1) & valid
    haze = (dm[..., 2] == 1) & valid
    shadow = (dm[..., 3] == 1) & valid
    clear = (dm[..., 0] == 1) & valid

    # quality mask coverage of the data footprint
    pq_valid = np.any(pq != 255, axis=-1)
    quality_mask_coverage_pct = round(100.0 * (valid & pq_valid).sum() / vtot, 2)

    # interpolated pixels (sensor artifact proxy) inside the valid footprint
    interp_total = int((pq[valid] == 1).sum())
    interp_pct = round(100.0 * interp_total / (vtot * n_bands), 4)
    per_band_interp = [int((pq[..., b][valid] == 1).sum()) for b in range(n_bands)]
    per_band_interp_pct = [
        round(100.0 * cnt / vtot, 4) for cnt in per_band_interp
    ]
    full_band_dropout = any(pct >= 100.0 for pct in per_band_interp_pct) or any(
        cnt == 0 and int((pq[..., b] == 255).sum()) == total_pixels for b, cnt in enumerate(per_band_interp)
    )

    return {
        "raster_height": int(dm.shape[0]),
        "raster_width": int(dm.shape[1]),
        "valid_footprint_pct": round(100.0 * valid.sum() / total_pixels, 2),
        "clear_pct": round(100.0 * clear.sum() / vtot, 2),
        "cloud_pct": round(100.0 * cloud.sum() / vtot, 2),
        "haze_pct": round(100.0 * haze.sum() / vtot, 2),
        "cloud_shadow_pct": round(100.0 * shadow.sum() / vtot, 2),
        "cloud_or_haze_pct": round(100.0 * (cloud | haze).sum() / vtot, 2),
        "quality_mask_coverage_pct": quality_mask_coverage_pct,
        "band_count": n_bands,
        "interpolated_pct": interp_pct,
        "interpolated_total": interp_total,
        "per_band_interpolated_pct": per_band_interp_pct,
        "full_band_dropout": full_band_dropout,
    }


def analyze_cog(cog_path: Path, data_mask_path: Path) -> dict:
    """Optional reflectance-level metrics (QA-6/QA-7) from the full band stack.

    Only used when a local COG is supplied. Reflectance = DN * scale (scale=0.0001).
    'Masked' pixels are excluded using the data mask's clear band (band 1) — PRD QA-6.

    QA-6: fraction of valid, unmasked band-pixels whose reflectance falls outside
          physical bounds [0, 1] (DN > 10000 with scale 0.0001).
    QA-7: mean pairwise Pearson correlation across bands on clear pixels. A
          well-calibrated hyperspectral stack has adjacent bands strongly correlated;
          a mean below the rule threshold signals internally inconsistent output.
    """
    import rasterio
    import numpy as np

    with rasterio.open(str(cog_path)) as ds:
        ov = ds.overviews(1)
        factor = ov[-1] if ov else 1
        shape = (ds.height // factor, ds.width // factor)
        scale = float(ds.scales[0]) if getattr(ds, "scales", None) and ds.scales[0] else 0.0001
        nodata = ds.nodata
        descriptions = list(ds.descriptions or [])

        raws = []
        for b in range(1, ds.count + 1):
            raws.append(ds.read(b, out_shape=(1, *shape)).squeeze().astype(np.float64))
        stack = np.stack(raws, axis=0)                 # (bands, H, W) raw DN

    with rasterio.open(str(data_mask_path)) as dm:
        clear = dm.read(1, out_shape=(1, *shape)).squeeze() == 1   # band 1 = clear

    nodata_mask = (stack == nodata) if nodata is not None else np.zeros(stack.shape, dtype=bool)
    valid = clear & (~nodata_mask).all(axis=0)
    valid_band_pixels = max(int(valid.sum()) * stack.shape[0], 1)

    reflectance = stack * scale

    # QA-6: reflectance outside [0, 1] on valid, unmasked band-pixels
    oob = ((reflectance < 0.0) | (reflectance > 1.0)) & valid[None, :, :]
    out_of_bounds_pct = round(100.0 * int(oob.sum()) / valid_band_pixels, 4)

    # QA-7: mean pairwise band correlation over clear pixels (sample if huge)
    sub = reflectance[:, valid]
    if sub.shape[1] > 200_000:                      # cap memory: subsample pixels
        idx = np.random.default_rng(42).choice(sub.shape[1], 200_000, replace=False)
        sub = sub[:, idx]
    corr = np.corrcoef(sub)
    n = corr.shape[0]
    triu = np.triu_indices(n, k=1)
    band_corr_mean = round(float(np.nanmean(corr[triu])), 4) if triu[0].size else None

    return {
        "reflectance_out_of_bounds_pct": out_of_bounds_pct,
        "band_corr_mean": band_corr_mean,
        "band_corr_min": round(float(np.nanmin(corr[triu])), 4) if triu[0].size else None,
    }


def compute_metrics(scene_dir: Path, cog_path: Path | None = None) -> tuple[dict, dict]:
    """Full pipeline for one scene directory → (scene_info, metrics)."""
    meta = load_stac_metadata(scene_dir / "stac_metadata.json")
    mask_metrics = analyze_masks(scene_dir / "data_mask.tiff", scene_dir / "pixel_quality_mask.tiff")

    # structural QA-1 pieces not available from ODP catalog metadata
    metrics = {
        "band_count": mask_metrics["band_count"],
        "aoi_coverage_pct": None,          # ODP items have no tasked-AOI record
        "quality_mask_coverage_pct": mask_metrics["quality_mask_coverage_pct"],
        "cloud_or_haze_pct": mask_metrics["cloud_or_haze_pct"],
        "interpolated_pct": mask_metrics["interpolated_pct"],
        "full_band_dropout": mask_metrics["full_band_dropout"],
        "geolocation_rmse_px": None,       # not published in Wyvern ODP STAC items
        "coreg_offset_px": None,           # not published in Wyvern ODP STAC items
        "reflectance_out_of_bounds_pct": None,
        "band_corr_mean": None,
    }

    if cog_path is not None:
        cog_metrics = analyze_cog(cog_path, scene_dir / "data_mask.tiff")
        metrics.update(cog_metrics)

    scene_info = {
        **meta,
        **mask_metrics,
    }
    return scene_info, metrics
