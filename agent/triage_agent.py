#!/usr/bin/env python3
"""
triage_agent.py — the QA triage agent.

Executes the PRD's QA rules (agent/rules.json, mirroring prd/qa-qc-prd.md §2-§4)
against each real scene in data/ and decides pass / retry / escalate with a
logged reasoning trace.

Usage:
    python triage_agent.py                          # run on all scenes in ../data
    python triage_agent.py --data ../data           # explicit data dir
    python triage_agent.py --cog <scene_id>=<path>  # supply a local COG for QA-6/QA-7
    python triage_agent.py --json                   # print machine-readable summary

Outputs:
    decisions.json  — structured decisions for the dashboard
    logs/<scene_id>.log — human-readable reasoning trace per scene
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from analyze_scene import compute_metrics, load_stac_metadata
from qa_rules import decide, evaluate_rule

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT.parent / "data"
DEFAULT_RULES = ROOT / "rules.json"
DEFAULT_OUT = ROOT / "decisions.json"
DEFAULT_LOG_DIR = ROOT / "logs"

# Role labels for the demo scenes (see data/README.md)
ROLE_BY_FOLDER = {
    "01-clean-cropfield-australia": "clean crop field (Australia)",
    "02-wildfire-smoke-saskatchewan": "wildfire smoke (Saskatchewan)",
    "03-copper-mine-chile": "open-pit copper mine (Chile)",
}


def discover_scenes(data_dir: Path) -> list[Path]:
    return sorted(p for p in data_dir.iterdir() if (p / "stac_metadata.json").exists())


def run_scene(scene_dir: Path, rules: dict, cog_map: dict[str, Path]) -> dict:
    scene_info, metrics = compute_metrics(scene_dir, cog_map.get(scene_dir.name))
    platform = rules["platforms"].get(scene_info["platform"], {})
    scene = {
        "processing_level": scene_info["processing_level"],
        "platform_spec": platform,
        "retry_count": 0,
        "max_retries": rules.get("max_retries", 2),
        "superseded": False,
    }

    evaluations = [evaluate_rule(r, metrics, scene) for r in rules["rules"]]
    decision = decide(evaluations, metrics, scene)

    return {
        "scene_id": scene_info["scene_id"],
        "folder": scene_dir.name,
        "role": ROLE_BY_FOLDER.get(scene_dir.name, "unknown"),
        "platform": scene_info["platform"],
        "datetime": scene_info["datetime"],
        "processing_level": scene_info["processing_level"],
        "processing_version": scene_info.get("processing_version"),
        "stac_cloud_cover_pct": scene_info.get("stac_cloud_cover_pct"),
        "gsd_m": scene_info.get("gsd_m"),
        "bbox": scene_info.get("bbox"),
        "cog_href": scene_info.get("cog_href"),
        "expected_bands": platform.get("expected_bands"),
        "metrics": metrics,
        "mask_metrics": {k: v for k, v in scene_info.items()
                         if k in ("valid_footprint_pct", "clear_pct", "cloud_pct", "haze_pct",
                                  "cloud_shadow_pct", "cloud_or_haze_pct",
                                  "quality_mask_coverage_pct", "interpolated_pct",
                                  "per_band_interpolated_pct", "full_band_dropout")},
        "rules": evaluations,
        "decision": decision["decision"],
        "failure_category": decision["failure_category"],
        "fired_rule": decision["fired_rule"],
        "reasoning": decision["reasoning"],
        "retry_count": decision["retry_count"],
        "version": "v1",
        "version_note": "Initial assessment. A retry that re-runs processing with changed parameters creates a new version (PRD §5); an automated retry with identical parameters is the same version, new attempt.",
        "delivery_ready": decision["delivery_ready"],
        "delivery_ready_note": decision["delivery_ready_note"],
        "not_assessed": decision["not_assessed"],
        "not_assessed_detail": decision["not_assessed_detail"],
    }


def write_log(record: dict, log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"Pixxel QA Triage Agent — reasoning trace",
        f"scene:  {record['scene_id']}",
        f"role:   {record['role']}",
        f"folder: {record['folder']}",
        f"platform: {record['platform']} (expected {record['expected_bands']} bands)",
        f"datetime: {record['datetime']}  level: {record['processing_level']}",
        f"STAC cloud cover: {record['stac_cloud_cover_pct']}%",
        "",
        "--- metrics ---",
    ]
    for k, v in record["metrics"].items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("--- rule evaluations (in PRD order) ---")
    for ev in record["rules"]:
        lines.append(f"  [{ev['status'].upper():15s}] {ev['rule_id']} {ev['name']} (levels {ev['level']})")
        for c in ev["checks"]:
            lines.append(f"        {c['metric']}: observed={c['observed']} threshold={c['threshold']} -> {c['status']}")
        lines.append(f"        → {ev['reasoning']}")
    lines.append("")
    lines.append(f"--- decision ---")
    lines.append(f"  outcome:          {record['decision'].upper()}")
    lines.append(f"  failure category: {record['failure_category']}")
    lines.append(f"  fired rule:       {record['fired_rule']}")
    lines.append(f"  reasoning:        {record['reasoning']}")
    lines.append(f"  retry count:      {record['retry_count']}")
    lines.append(f"  version:          {record['version']}")
    lines.append(f"  delivery ready:   {record['delivery_ready']} — {record['delivery_ready_note']}")
    if record["not_assessed"]:
        lines.append(f"  NOT ASSESSED:     {record['not_assessed']}")
        for d in record["not_assessed_detail"]:
            lines.append(f"        {d}")
    (log_dir / f"{record['scene_id']}.log").write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Pixxel QA triage agent")
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    ap.add_argument("--cog", action="append", default=[], metavar="FOLDER=PATH",
                    help="supply a local band stack (COG) for a scene folder, e.g. 01-clean-cropfield-australia=/abs/path.tiff")
    ap.add_argument("--json", action="store_true", help="print machine-readable summary to stdout")
    args = ap.parse_args()

    rules = json.loads(args.rules.read_text())
    cog_map = {}
    for spec in args.cog:
        folder, _, path = spec.partition("=")
        cog_map[folder.strip()] = Path(path.strip())

    scene_dirs = discover_scenes(args.data)
    if not scene_dirs:
        print(f"no scene folders (with stac_metadata.json) found under {args.data}", file=sys.stderr)
        return 1

    records = [run_scene(d, rules, cog_map) for d in scene_dirs]
    payload = {
        "schema": "pixxel.qa.decisions.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rules_source": "prd/qa-qc-prd.md §2-§4 (agent/rules.json)",
        "max_retries": rules.get("max_retries"),
        "scenes": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))

    for r in records:
        write_log(r, args.log_dir)

    print(f"wrote {args.out}")
    print(f"wrote {len(records)} reasoning logs to {args.log_dir}")
    print()
    print(f"{'scene':<58s} {'decision':<9s} {'cat':<9s} {'rule':<6s} {'retry':<5s} {'ready':<6s} {'not assessed'}")
    for r in records:
        print(f"{r['scene_id'][:56]:<58s} {r['decision']:<9s} {str(r['failure_category']):<9s} "
              f"{str(r['fired_rule']):<6s} {r['retry_count']:<5d} {str(r['delivery_ready']):<6s} {','.join(r['not_assessed'])}")
    if args.json:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
