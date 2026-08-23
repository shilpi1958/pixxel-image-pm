"""
test_qa_rules.py — verify the QA rule engine and metric computations on
synthetic inputs. Run with:  python -m pytest agent/tests  (or python agent/tests/test_qa_rules.py)

Covers:
  * every rule: pass / fail / not_assessable / not_applicable paths
  * decision synthesis: clean pass, cloud retry, retry ceiling -> escalate,
    mask gap -> escalate, L1B band-count failure -> escalate
  * analyze_cog: QA-6 (reflectance out of bounds) and QA-7 (band correlation)
    from a synthetic band stack + clear mask
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qa_rules import decide, evaluate_rule  # noqa: E402

RULES = json.loads((ROOT / "rules.json").read_text())
L2A = {"processing_level": "L2A", "platform_spec": RULES["platforms"]["Dragonette-003"],
       "retry_count": 0, "max_retries": RULES["max_retries"], "superseded": False}
L1B = dict(L2A, processing_level="L1B")
# Dragonette-001: 23 expected bands (used for QA-1/QA-4 L1B tests)
L1B_D1 = dict(L1B, platform_spec=RULES["platforms"]["Dragonette-001"])


def eval_all(metrics: dict, scene: dict) -> list[dict]:
    return [evaluate_rule(r, metrics, scene) for r in RULES["rules"]]


def test_clean_l2a_passes():
    metrics = {"band_count": 31, "quality_mask_coverage_pct": 100.0, "cloud_or_haze_pct": 0.0,
               "interpolated_pct": 0.0, "full_band_dropout": False,
               "reflectance_out_of_bounds_pct": 0.0, "band_corr_mean": 0.99}
    ev = eval_all(metrics, L2A)
    failed = [e for e in ev if e["status"] == "fail"]
    assert failed == []
    d = decide(ev, metrics, L2A)
    assert d["decision"] == "pass"
    assert d["delivery_ready"] is True
    assert d["retry_count"] == 0


def test_cloud_retry():
    metrics = {"band_count": 31, "quality_mask_coverage_pct": 100.0, "cloud_or_haze_pct": 62.3,
               "interpolated_pct": 0.0, "full_band_dropout": False,
               "reflectance_out_of_bounds_pct": 0.0, "band_corr_mean": 0.99}
    ev = eval_all(metrics, L2A)
    d = decide(ev, metrics, L2A)
    assert d["decision"] == "retry"
    assert d["failure_category"] == "CLOUD"
    assert d["fired_rule"] == "QA-3"
    assert d["retry_count"] == 1
    assert d["delivery_ready"] is False


def test_retry_ceiling_escalates():
    metrics = {"band_count": 31, "quality_mask_coverage_pct": 100.0, "cloud_or_haze_pct": 62.3,
               "interpolated_pct": 0.0, "full_band_dropout": False,
               "reflectance_out_of_bounds_pct": 0.0, "band_corr_mean": 0.99}
    scene = dict(L2A, retry_count=2)   # already at MAX_RETRIES
    ev = eval_all(metrics, scene)
    d = decide(ev, metrics, scene)
    assert d["decision"] == "escalate"
    assert d["failure_category"] == "CLOUD"


def test_mask_gap_escalates():
    metrics = {"band_count": 31, "quality_mask_coverage_pct": 92.0, "cloud_or_haze_pct": 0.0,
               "interpolated_pct": 0.0, "full_band_dropout": False,
               "reflectance_out_of_bounds_pct": 0.0, "band_corr_mean": 0.99}
    ev = eval_all(metrics, L2A)
    d = decide(ev, metrics, L2A)
    assert d["decision"] == "escalate"
    assert d["failure_category"] == "MASK_GAP"
    assert d["fired_rule"] == "QA-2"   # first failing rule in order


def test_l1b_band_count_fail_escalates():
    metrics = {"band_count": 20, "quality_mask_coverage_pct": 100.0, "cloud_or_haze_pct": 0.0,
               "interpolated_pct": 0.0, "full_band_dropout": False,
               "reflectance_out_of_bounds_pct": 0.0, "band_corr_mean": 0.99}
    ev = eval_all(metrics, L1B_D1)
    d = decide(ev, metrics, L1B_D1)
    assert d["decision"] == "escalate"
    assert d["failure_category"] == "INCOMPLETE"
    assert d["fired_rule"] == "QA-1"


def test_l1b_sensor_artifact_escalates():
    metrics = {"band_count": 23, "quality_mask_coverage_pct": 100.0, "cloud_or_haze_pct": 0.0,
               "interpolated_pct": 5.0, "full_band_dropout": False,
               "reflectance_out_of_bounds_pct": 0.0, "band_corr_mean": 0.99}
    ev = eval_all(metrics, L1B_D1)
    d = decide(ev, metrics, L1B_D1)
    assert d["decision"] == "escalate"
    assert d["failure_category"] == "SENSOR"
    assert d["fired_rule"] == "QA-4"


def test_full_band_dropout_fires_sensor():
    metrics = {"band_count": 23, "quality_mask_coverage_pct": 100.0, "cloud_or_haze_pct": 0.0,
               "interpolated_pct": 0.0, "full_band_dropout": True,
               "reflectance_out_of_bounds_pct": 0.0, "band_corr_mean": 0.99}
    ev = eval_all(metrics, L1B_D1)
    d = decide(ev, metrics, L1B_D1)
    assert d["decision"] == "escalate"
    assert d["fired_rule"] == "QA-4"


def test_geometric_misalignment_retry():
    metrics = {"band_count": 31, "quality_mask_coverage_pct": 100.0, "cloud_or_haze_pct": 0.0,
               "interpolated_pct": 0.0, "full_band_dropout": False,
               "geolocation_rmse_px": 2.1, "coreg_offset_px": 0.1,
               "reflectance_out_of_bounds_pct": 0.0, "band_corr_mean": 0.99}
    ev = eval_all(metrics, L2A)
    d = decide(ev, metrics, L2A)
    assert d["decision"] == "retry"
    assert d["failure_category"] == "GEOM"
    assert d["fired_rule"] == "QA-5"


def test_radiometric_bounds_retry():
    metrics = {"band_count": 31, "quality_mask_coverage_pct": 100.0, "cloud_or_haze_pct": 0.0,
               "interpolated_pct": 0.0, "full_band_dropout": False,
               "reflectance_out_of_bounds_pct": 3.2, "band_corr_mean": 0.99}
    ev = eval_all(metrics, L2A)
    d = decide(ev, metrics, L2A)
    assert d["decision"] == "retry"
    assert d["failure_category"] == "RADIO"
    assert d["fired_rule"] == "QA-6"


def test_radiometric_consistency_escalates():
    metrics = {"band_count": 31, "quality_mask_coverage_pct": 100.0, "cloud_or_haze_pct": 0.0,
               "interpolated_pct": 0.0, "full_band_dropout": False,
               "reflectance_out_of_bounds_pct": 0.0, "band_corr_mean": 0.45}
    ev = eval_all(metrics, L2A)
    d = decide(ev, metrics, L2A)
    assert d["decision"] == "escalate"
    assert d["failure_category"] == "RADIO"
    assert d["fired_rule"] == "QA-7"


def test_missing_metrics_reported_not_assessable():
    metrics = {"band_count": 31}   # everything else missing
    ev = eval_all(metrics, L2A)
    statuses = {e["rule_id"]: e["status"] for e in ev}
    assert statuses["QA-2"] == "not_assessable"
    assert statuses["QA-3"] == "not_assessable"
    assert statuses["QA-5"] == "not_assessable"
    d = decide(ev, metrics, L2A)
    assert d["decision"] == "pass"
    assert "QA-5" in d["not_assessed"] and "QA-6" in d["not_assessed"]


def test_not_applicable_at_level():
    ev = eval_all({"band_count": 20}, L1B)  # QA-6/7 are L2A-only
    statuses = {e["rule_id"]: e["status"] for e in ev}
    assert statuses["QA-6"] == "not_applicable"
    assert statuses["QA-7"] == "not_applicable"
    assert statuses["QA-1"] == "fail"       # L1B band-count failure still fires


def test_analyze_cog_metrics():
    """Exercise QA-6/QA-7 on a synthetic band stack + clear mask."""
    from analyze_scene import analyze_cog

    tmp = ROOT / "tests" / "_tmp_cog"
    tmp.mkdir(parents=True, exist_ok=True)

    import rasterio
    from rasterio.transform import from_origin

    h, w, nbands = 40, 50, 6
    scale = 0.0001

    # clean synthetic scene: smooth bands (high correlation), all in [0,1]
    base = np.abs(np.random.default_rng(7).normal(0.25, 0.08, size=(h, w)))
    clean = np.stack([base + i * 0.01 for i in range(nbands)], axis=0)
    clean_dn = np.clip(np.round(clean / scale), 0, 10000).astype(np.uint16)

    # corrupt a patch: 3% of pixels saturated out of bounds (DN > 10000)
    corrupt = clean_dn.copy()
    mask_xy = np.random.default_rng(1).choice(h * w, int(0.05 * h * w), replace=False)
    corrupt.reshape(nbands, -1)[:, mask_xy] = 14000

    cog_path = tmp / "synthetic.tiff"
    with rasterio.open(
        cog_path, "w", driver="GTiff", height=h, width=w, count=nbands,
        dtype="uint16", transform=from_origin(0, 0, 1, 1), scales=[scale] * nbands,
    ) as ds:
        for b in range(1, nbands + 1):
            ds.write(corrupt[b - 1], b)

    dm_path = tmp / "synthetic_data_mask.tiff"
    dm = np.zeros((h, w, 4), dtype=np.uint8)
    dm[..., 0] = 1        # clear everywhere
    dm[..., 1] = 0        # no cloud
    dm[..., 2] = 0
    dm[..., 3] = 0
    tifffile = __import__("tifffile")
    tifffile.imwrite(dm_path, dm, photometric="minisblack")

    m = analyze_cog(cog_path, dm_path)
    assert m["reflectance_out_of_bounds_pct"] > 0.5, m
    assert m["band_corr_mean"] > 0.9, m   # clean stack is highly correlated

    # now a decorrelated stack -> QA-7 would fire
    noisy = np.stack([np.abs(np.random.default_rng(i).normal(0.3, 0.2, size=(h, w))) for i in range(nbands)], axis=0)
    noisy_dn = np.clip(np.round(noisy / scale), 0, 10000).astype(np.uint16)
    with rasterio.open(
        cog_path, "w", driver="GTiff", height=h, width=w, count=nbands,
        dtype="uint16", transform=from_origin(0, 0, 1, 1), scales=[scale] * nbands,
    ) as ds:
        for b in range(1, nbands + 1):
            ds.write(noisy_dn[b - 1], b)
    m2 = analyze_cog(cog_path, dm_path)
    assert m2["band_corr_mean"] < 0.7, m2


if __name__ == "__main__":
    import traceback

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Exception:
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(fns)} tests passed")
    sys.exit(0 if passed == len(fns) else 1)
