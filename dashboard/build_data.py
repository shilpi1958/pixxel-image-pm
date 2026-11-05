#!/usr/bin/env python3
"""
build_data.py — generate dashboard/data.js from the agent's real output.

The dashboard is a dependency-free single page. To keep it clickable even when
opened straight from disk (file://), the scene data is embedded as a JS object
rather than fetched at runtime.

Usage:
    python dashboard/build_data.py            # reads ../agent/decisions.json
    python dashboard/build_data.py --out dashboard/data.js
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# A short human label + PRD anchor per rule, for the dashboard detail view.
RULE_LABELS = {
    "QA-1": ("Incomplete data", "PRD §3 QA-1 — escalate"),
    "QA-2": ("Quality mask gap", "PRD §3 QA-2 — escalate"),
    "QA-3": ("Cloud/haze obstruction", "PRD §3 QA-3 — retry (re-task if > 80%)"),
    "QA-4": ("Sensor artifact", "PRD §3 QA-4 — escalate"),
    "QA-5": ("Geometric misalignment", "PRD §3 QA-5 — retry"),
    "QA-6": ("Radiometric bounds", "PRD §3 QA-6 — retry"),
    "QA-7": ("Radiometric consistency", "PRD §3 QA-7 — escalate"),
}

# Domain-context notes, not agent output — hand-written annotations for scenes
# where a specific finding is worth surfacing. Keyed by folder name.
SCENE_NOTES = {
    "03-copper-mine-chile": [
        "Real finding from this project: pixels flagged as interpolated in Wyvern's pixel quality "
        "mask appear only in bands 13/15/16 (679/699/711nm) — the red / red-edge boundary",
        "Each band's flagged pixels form a thin diagonal stripe (~10% of image height, ~71% of width), "
        "at different rows per band — ~31% of image height combined. Not scattered noise; consistent "
        "with missing scan lines, which Wyvern says it fills by interpolation (cause not confirmed)",
    ],
}

METRIC_LABELS = {
    "band_count": "Band count",
    "aoi_coverage_pct": "AOI coverage %",
    "quality_mask_coverage_pct": "Quality-mask coverage of scene footprint %",
    "cloud_or_haze_pct": "Cloud + haze (smoke) % of valid pixels",
    "interpolated_pct": "Interpolated pixels % (of band-pixels)",
    "full_band_dropout": "Full-band dropout",
    "max_high_value_band_interpolated_pct": "Worst red-edge band (711-782nm) interpolated %",
    "geolocation_rmse_px": "Geolocation RMSE (px)",
    "coreg_offset_px": "Cross-band co-registration offset (px)",
    "reflectance_out_of_bounds_pct": "Reflectance outside [0,1] %",
    "band_corr_mean": "Mean band-to-band correlation",
    "band_corr_min_tile": "Worst spatial-tile band correlation",
}


# What each data source contributes, and how to detect it's present for a
# given scene. Order here is the order shown in the dashboard's data-inventory
# grid, roughly cheapest/broadest evidence first, deepest/rarest last.
DATA_SOURCES = [
    ("imagery", "Imagery", "RGB preview + thumbnail", ["preview.png", "thumbnail.png"]),
    ("stac", "Metadata", "STAC metadata (platform, bands, cloud cover, geometry)", ["stac_metadata.json", "item.json"]),
    ("data_mask", "Data mask", "Usable-data mask (cloud/haze/shadow, real TIFF)", ["data_mask.tiff"]),
    ("quality_mask", "Quality mask", "Pixel quality mask (interpolated pixels per band, real TIFF)", ["pixel_quality_mask.tiff"]),
    ("band_stack", "Band stack", "Full band-stack reflectance pull (QA-6/QA-7 spot-checked against real values)", ["band_stack_analysis.json"]),
]


def data_inventory(data_dir: Path) -> list[dict]:
    inventory = []
    for key, label, title, filenames in DATA_SOURCES:
        present = any((data_dir / f).exists() for f in filenames)
        inventory.append({"key": key, "label": label, "title": title, "present": present})
    return inventory


def build(decisions_path: Path, data_root: Path, out_path: Path) -> None:
    decisions = json.loads(decisions_path.read_text())
    scenes = []
    for s in decisions["scenes"]:
        scenes.append({
            "scene_id": s["scene_id"],
            "folder": s["folder"],
            "role": s["role"],
            "platform": s["platform"],
            "datetime": s["datetime"],
            "processing_level": s["processing_level"],
            "processing_version": s.get("processing_version"),
            "stac_cloud_cover_pct": s.get("stac_cloud_cover_pct"),
            "gsd_m": s.get("gsd_m"),
            "expected_bands": s.get("expected_bands"),
            "decision": s["decision"],
            "failure_category": s["failure_category"],
            "fired_rule": s["fired_rule"],
            "reasoning": s["reasoning"],
            "retry_count": s["retry_count"],
            "version": s["version"],
            "version_note": s.get("version_note"),
            "delivery_ready": s["delivery_ready"],
            "delivery_ready_partial": s.get("delivery_ready_partial", False),
            "excluded_bands": s.get("excluded_bands", []),
            "delivery_ready_note": s["delivery_ready_note"],
            "not_assessed": s["not_assessed"],
            "not_assessed_detail": s["not_assessed_detail"],
            "band_stack_source": s.get("band_stack_source"),
            "metrics": [{"key": k, "label": METRIC_LABELS.get(k, k), "value": v} for k, v in s["metrics"].items()],
            "mask_metrics": s.get("mask_metrics", {}),
            "rules": [
                {
                    "rule_id": r["rule_id"],
                    "name": RULE_LABELS.get(r["rule_id"], (r["name"], ""))[0],
                    "anchor": RULE_LABELS.get(r["rule_id"], ("", ""))[1],
                    "status": r["status"],
                    "category": r["category"],
                    "routing": r["routing"],
                    "reasoning": r["reasoning"],
                    "checks": r["checks"],
                }
                for r in s["rules"]
            ],
            "preview": f"../data/{s['folder']}/preview.png",
            "thumbnail": f"../data/{s['folder']}/thumbnail.png",
            "data_mask_preview": f"../data/{s['folder']}/data_mask_preview.png",
            "quality_mask_preview": f"../data/{s['folder']}/quality_mask_preview.png",
            "data_dir": f"../data/{s['folder']}/",
            "scene_note": SCENE_NOTES.get(s["folder"]),
            "data_inventory": data_inventory(data_root / s["folder"]),
        })

    payload = {
        "schema": "pixxel.qa.dashboard.v1",
        "generated_at": decisions.get("generated_at") or datetime.now(timezone.utc).isoformat(),
        "rules_source": decisions.get("rules_source"),
        "max_retries": decisions.get("max_retries"),
        "scene_count": len(scenes),
        "summary": {
            "pass": sum(1 for s in scenes if s["decision"] == "pass"),
            "retry": sum(1 for s in scenes if s["decision"] == "retry"),
            "escalate": sum(1 for s in scenes if s["decision"] == "escalate"),
        },
        "scenes": scenes,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "/* Auto-generated by dashboard/build_data.py from agent/decisions.json. Do not edit. */\n"
        "window.PIXXEL_DATA = " + json.dumps(payload, indent=2) + ";\n"
    )
    print(f"wrote {out_path} ({out_path.stat().st_size // 1024} KB, {len(scenes)} scenes)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", type=Path, default=ROOT.parent / "agent" / "decisions.json")
    ap.add_argument("--data-root", type=Path, default=ROOT.parent / "data")
    ap.add_argument("--out", type=Path, default=ROOT / "data.js")
    args = ap.parse_args()
    build(args.decisions, args.data_root, args.out)
