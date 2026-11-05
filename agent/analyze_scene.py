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


def high_value_band_indices(eo_bands: list[dict], lo_nm: float = 711, hi_nm: float = 782) -> list[int]:
    """Indices of eo_bands whose center_wavelength falls in [lo_nm, hi_nm] (PRD §3).

    Wavelength-based, not position-based: band count and ordering differ between
    the 23-band (Dragonette-001) and 31-band (Dragonette-002/003/004) platforms.
    """
    out = []
    for i, b in enumerate(eo_bands):
        wl_nm = b.get("center_wavelength")
        if wl_nm is None:
            continue
        wl_nm = wl_nm * 1000 if wl_nm < 10 else wl_nm  # STAC stores micrometers (e.g. 0.711)
        if lo_nm <= wl_nm <= hi_nm:
            out.append(i)
    return out


def analyze_masks(data_mask_path: Path, pq_mask_path: Path, eo_bands: list[dict] | None = None) -> dict:
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

    # PRD §3: worst single high-value (red-edge) band's interpolated %, not just the scene-wide average.
    hv_indices = high_value_band_indices(eo_bands) if eo_bands else []
    hv_indices = [i for i in hv_indices if i < len(per_band_interp_pct)]
    max_hv_interp_pct = round(max((per_band_interp_pct[i] for i in hv_indices), default=0.0), 4)

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
        "high_value_band_indices": hv_indices,
        "max_high_value_band_interpolated_pct": max_hv_interp_pct,
    }


def analyze_cog(cog_path: Path, data_mask_path: Path, scale: float | None = None) -> dict:
    """Optional reflectance-level metrics (QA-6/QA-7) from the full band stack.

    Only used when a local COG is supplied. Reflectance = DN * scale.
    IMPORTANT: Wyvern's COG files do NOT embed a reliable scale in the TIFF
    tags (rasterio reports 1.0); the authoritative scale is declared in the
    STAC metadata (raster:bands[].scale = 0.0001) and passed in via `scale`.
    'Masked' pixels are excluded using the data mask's clear band (band 1) — PRD QA-6.

    QA-6: fraction of valid, unmasked band-pixels whose reflectance falls outside
          physical bounds [0, 1]. Computed exactly, band by band, so the
          multi-GB stacks never need to fit in memory at once.
    QA-7: mean pairwise Pearson correlation across bands on clear pixels (random
          subsample of at most 200k pixels). A well-calibrated hyperspectral stack
          has adjacent bands strongly correlated; a mean below the rule threshold
          signals internally inconsistent output.
    """
    import rasterio
    import numpy as np

    with rasterio.open(str(cog_path)) as ds:
        n_bands = ds.count
        h, w = ds.height, ds.width
        if scale is None:
            scale = float(ds.scales[0]) if getattr(ds, "scales", None) and ds.scales[0] else 0.0001
        nodata = ds.nodata

        with rasterio.open(str(data_mask_path)) as dm:
            clear = dm.read(1, out_shape=(1, h, w)).squeeze() == 1   # band 1 = clear

        # ---- QA-6: exact per-band pass (one band in memory at a time) ----
        oob_total = 0
        valid_total = 0
        for b in range(1, n_bands + 1):
            band = ds.read(b)                       # full-res uint16, transient
            valid_b = clear & (band != nodata) if nodata is not None else clear
            refl_b = band.astype(np.float64) * scale
            oob_total += int(((refl_b < 0.0) | (refl_b > 1.0))[valid_b].sum())
            valid_total += int(valid_b.sum())
        out_of_bounds_pct = round(100.0 * oob_total / max(valid_total, 1), 4)

        # ---- QA-7: correlation on a random subsample of clear pixels ----
        n_px = 200_000
        flat_clear = np.flatnonzero(clear)
        if flat_clear.size > n_px:
            idx = np.random.default_rng(42).choice(flat_clear.size, n_px, replace=False)
            px = flat_clear[idx]
        else:
            px = flat_clear
        rows, cols = np.unravel_index(px, (h, w))

        sample = np.empty((n_bands, px.size), dtype=np.float64)
        for b in range(1, n_bands + 1):
            band = ds.read(b)
            sample[b - 1] = band[rows, cols].astype(np.float64) * scale
        if nodata is not None:
            good = (sample != nodata * scale).all(axis=0)
            sample, rows, cols = sample[:, good], rows[good], cols[good]

        corr = np.corrcoef(sample)
        triu = np.triu_indices(n_bands, k=1)
        band_corr_mean = round(float(np.nanmean(corr[triu])), 4) if triu[0].size else None
        band_corr_min = round(float(np.nanmin(corr[triu])), 4) if triu[0].size else None

        # ---- PRD §3: same correlation, computed per spatial tile (8x8 grid) ----
        # A scene-wide average can dilute a localized inconsistency; the worst tile
        # is what QA-7's band_corr_min_tile check looks at (looser threshold —
        # each tile has far fewer sampled pixels, so its estimate is noisier).
        n_tiles_side = 8
        tile_h, tile_w = max(h // n_tiles_side, 1), max(w // n_tiles_side, 1)
        tile_row = np.minimum(rows // tile_h, n_tiles_side - 1)
        tile_col = np.minimum(cols // tile_w, n_tiles_side - 1)
        tile_id = tile_row * n_tiles_side + tile_col

        band_corr_min_tile = None
        MIN_PIXELS_PER_TILE = 50  # skip tiles too sparse for a meaningful correlation estimate
        for t in np.unique(tile_id):
            mask_t = tile_id == t
            if mask_t.sum() < MIN_PIXELS_PER_TILE:
                continue
            corr_t = np.corrcoef(sample[:, mask_t])
            triu_t = np.triu_indices(n_bands, k=1)
            if not triu_t[0].size:
                continue
            mean_t = float(np.nanmean(corr_t[triu_t]))
            if band_corr_min_tile is None or mean_t < band_corr_min_tile:
                band_corr_min_tile = mean_t
        band_corr_min_tile = round(band_corr_min_tile, 4) if band_corr_min_tile is not None else None

    return {
        "reflectance_out_of_bounds_pct": out_of_bounds_pct,
        "band_corr_mean": band_corr_mean,
        "band_corr_min": band_corr_min,
        "band_corr_min_tile": band_corr_min_tile,
    }


def compute_metrics(scene_dir: Path, cog_path: Path | None = None) -> tuple[dict, dict]:
    """Full pipeline for one scene directory → (scene_info, metrics)."""
    meta = load_stac_metadata(scene_dir / "stac_metadata.json")
    mask_metrics = analyze_masks(
        scene_dir / "data_mask.tiff", scene_dir / "pixel_quality_mask.tiff", eo_bands=meta.get("eo_bands")
    )

    # structural QA-1 pieces not available from ODP catalog metadata
    metrics = {
        "band_count": mask_metrics["band_count"],
        "aoi_coverage_pct": None,          # ODP items have no tasked-AOI record
        "quality_mask_coverage_pct": mask_metrics["quality_mask_coverage_pct"],
        "aoi_cloud_or_haze_pct": None,     # no tasked AOI, so QA-3 falls back to scene-wide
        "cloud_or_haze_pct": mask_metrics["cloud_or_haze_pct"],
        "interpolated_pct": mask_metrics["interpolated_pct"],
        "full_band_dropout": mask_metrics["full_band_dropout"],
        "max_high_value_band_interpolated_pct": mask_metrics["max_high_value_band_interpolated_pct"],  # PRD §3
        "geolocation_rmse_px": None,       # not published in Wyvern ODP STAC items
        "coreg_offset_px": None,           # not published in Wyvern ODP STAC items
        "reflectance_out_of_bounds_pct": None,
        "band_corr_mean": None,
        "band_corr_min_tile": None,        # PRD §3 — requires --cog (COG-derived, see analyze_cog)
    }

    band_stack_source = None
    if cog_path is not None:
        cog_metrics = analyze_cog(
            cog_path,
            scene_dir / "data_mask.tiff",
            scale=meta.get("cog_scale"),      # STAC-declared scale (file tags are unreliable)
        )
        # Only the three metrics QA-6/QA-7 actually check; band_corr_min (the
        # single worst global band pair) is diagnostic-only, not a rule input.
        metrics.update({k: v for k, v in cog_metrics.items() if k in metrics})
        band_stack_source = "live --cog pull, this run"
    else:
        # The full band stack (2+ GB) isn't mirrored in this repo (see data/README.md).
        # If a prior one-off pull already computed these three metrics against the
        # real raster, reuse them rather than leaving the rule not-assessable —
        # but keep it visibly separate from this run's own computation.
        analysis_path = scene_dir / "band_stack_analysis.json"
        if analysis_path.exists():
            analysis = json.loads(analysis_path.read_text())
            metrics["reflectance_out_of_bounds_pct"] = analysis.get("qa6_reflectance_out_of_bounds_pct")
            metrics["band_corr_mean"] = analysis.get("qa7_band_corr_mean")
            metrics["band_corr_min_tile"] = analysis.get("qa7_band_corr_min_tile")
            band_stack_source = f"prior one-off pull, recorded in {analysis_path.name}"

    scene_info = {
        **meta,
        **mask_metrics,
        "band_stack_source": band_stack_source,
    }
    return scene_info, metrics
