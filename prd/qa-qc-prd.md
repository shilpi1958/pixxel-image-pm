# QA/QC PRD — Hyperspectral Image Pipeline Monitoring

- **Owner:** Image Product Manager (pipeline monitoring layer)
- **Scope:** QA/QC, failure categorization, retry/hold/re-task/escalation, delivery-readiness
- Covers raw capture (L0/L1B) through delivered product (L2A+)
- **Out of scope:** the image-processing algorithms themselves (calibration, atmospheric correction, orthorectification, co-registration)
- This PRD defines pass/fail and what happens in response, not how the algorithms work internally

---

## 1. Processing levels

| Level | Description | QA applies? |
|---|---|---|
| L0 | Raw sensor telemetry | No — QA starts at L1B |
| L1B | Calibrated, geolocated, not atmospherically corrected | Yes — structural/sensor QA |
| L2A | Atmospherically corrected, surface reflectance | Yes — full QA, delivery product |

---

## 2. Failure categories

- Every failure gets exactly one primary category
- A scene can have multiple failures, one category each
- No failures across all categories → `CLEAN`

| Code | Category | Definition | Level |
|---|---|---|---|
| `CLOUD` | Cloud/atmospheric obstruction | Cloud, haze, or smoke coverage exceeds threshold | L1B, L2A |
| `SENSOR` | Sensor artifact | Striping, dead pixels, band dropout, saturation, or a single high-value band exceeding its own tighter ceiling | L1B, L2A |
| `GEOM` | Geometric misalignment | Geolocation or co-registration error exceeds tolerance | L1B, L2A |
| `RADIO` | Radiometric anomaly | Reflectance outside physical range, internally inconsistent overall, or inconsistent within a spatial tile | L2A |
| `MASK_GAP` | Missing/incomplete quality mask | Mask absent, malformed, or partial coverage | L1B, L2A |
| `INCOMPLETE` | Incomplete data | Band count below spec, or coverage below tasked AOI | L1B |

- `SENSOR`'s pixel_quality_mask is delivered on L2A products in this catalog, so the category applies at both levels

---

## 3. QA pass/fail rules

- Evaluated in order; first failing rule decides the outcome
- Thresholds are placeholders, tuned against real data
- Every rule is mechanical, not a judgment call

| Rule | Level | Condition | Category | Outcome |
|---|---|---|---|---|
| QA-1 | L1B | Band count < platform spec, or coverage < 95% of AOI | `INCOMPLETE` | Escalate |
| QA-2 | L1B/L2A | Quality mask missing/unparseable/< 100% coverage | `MASK_GAP` | Escalate |
| QA-3 | L1B/L2A | Cloud/haze/smoke > 40% of the tasked AOI (scene-wide if no AOI) | `CLOUD` | Hold (> 40%) · Re-task (> 80%) |
| QA-4 | L1B/L2A | Dead/saturated > 2% scene-wide, full-band dropout, **or** any single 711–782nm band interpolated > 0.1% | `SENSOR` | Escalate |
| QA-5 | L1B/L2A | Geolocation RMSE > 1px, or co-registration offset > 0.5px | `GEOM` | Retry |
| QA-6 | L2A | Reflectance outside [0,1] for > 0.5% of valid pixels | `RADIO` | Retry |
| QA-7 | L2A | Band-to-band correlation < 0.7 scene-wide, **or** < 0.5 in any single spatial tile (8×8 grid) | `RADIO` | Escalate |
| — | — | No rule fired | `CLEAN` | Pass |

- Fixable, mechanical problems (bad geolocation, out-of-range reflectance) → **retry** (reprocess)
- Cloud → **hold** or **re-task**, never reprocess — cloud is baked into the capture, so re-running processing returns the same result
- Problems reprocessing can't fix (missing bands, dead sensor pixels, self-contradicting output) → **escalate**
- QA-7 always escalates — needs human judgment, not another automated pass
- QA-3 measures cloud over the customer's tasked AOI when one exists — a strip can be 60% cloudy overall and clear over the field that was ordered. Open-data scenes have no AOI, so QA-3 falls back to scene-wide
- QA-3's 40–80% band holds rather than re-tasks — enough ground may be usable for the customer's purpose, so they decide
- QA-4's per-band condition exists because a defect confined to a few high-value (711–782nm, the red-edge range) bands can be a tiny fraction of the scene-wide average and still pass
- QA-4's band list is wavelength-based, not index-based — indices shift between the 23-band and 31-band platforms (`agent/rules.json` → `platforms`)
- QA-7's per-tile condition exists because a small localized defect is diluted by the rest of the clean pixels and can look fine in a scene-wide average
- QA-7's tile threshold (0.5) is looser than its scene-wide threshold (0.7) — a smaller sample per tile is naturally noisier; the goal is catching a badly inconsistent tile, not flagging normal variance

---

## 4. Retry, hold, re-task, escalate

| Outcome | Means | Fixes |
|---|---|---|
| **Retry** | Reprocess the same capture | Processing-parameter problems (`GEOM`, QA-6 `RADIO`) |
| **Hold** | Deliver nothing yet; customer accepts as-is or asks for re-task | Moderate cloud (QA-3, 40–80%) |
| **Re-task** | Schedule a new capture of the AOI | Heavy cloud (QA-3, > 80%) |
| **Escalate** | Ticket to on-call human | Problems no automated step can fix |

**Retry** when:
- Category is `GEOM`/`RADIO` (except QA-7)
- Retry count < `MAX_RETRIES` (default 2)
- The failure is plausibly transient/parameter-fixable
- On retry: increment count, log the rule, re-run only the affected processing stage

**Hold / re-task** when:
- QA-3 fires (`CLOUD`)
- Neither consumes retries — reprocessing can't change the result, so the retry budget isn't spent on it
- On hold: notify the customer with the measured cloud %, scene held until they respond
- On re-task: request a new capture of the AOI; this scene is superseded once the new one arrives
- Exception: if the cloud mask itself looks wrong (e.g. "cloud" over a known salt flat or snowfield), that's a reprocess with a different cloud classifier — a human call, raised from the hold

**Escalate** when:
- Category is `INCOMPLETE`/`SENSOR`/`MASK_GAP`
- Or retry ceiling reached
- Or QA-7 fires
- On escalate: open a ticket with scene ID, category, rule, full trace
- Assign to on-call
- Scene held, not delivered

**Ceiling:** at `MAX_RETRIES`, the system must escalate — silent infinite retry is a pipeline bug. The ceiling applies to retries (reprocessing) only.

---

## 5. Delivery-ready definition

Delivery ready requires:
- `CLEAN` status
- L2A
- Quality mask at 100% coverage
- Not superseded by a newer version

- A `CLEAN` scene under a pending escalation from an *earlier* version is still not delivery-ready until that's resolved

**Partial delivery — `delivery_ready_partial`:** weaker than full `delivery_ready` — ships a scene with an `excluded_bands` list when QA-4's per-band check is the *sole* failure and the customer has opted in at the account level. Not available for QA-3/5/6/7 failures, which aren't band-isolable.

---

## 6. How the metrics behind these rules are computed

- This PRD defines the rules and thresholds; it does not define the computation itself
- Every metric below is derived step-by-step, on real scene data, in [`notebooks/qa_pipeline_walkthrough.ipynb`](../notebooks/qa_pipeline_walkthrough.ipynb)
- The notebook also re-runs the actual rule engine (`agent/analyze_scene.py`, `agent/qa_rules.py`) and checks its output against what's committed in `agent/decisions.json`
- Results, per-scene findings, and the full rule-by-rule evaluation live in the [dashboard](../dashboard/)

| Metric | Feeds | Meaning |
|---|---|---|
| `band_count` | QA-1 | Number of spectral bands in the pixel quality mask, checked against the platform's expected count |
| `aoi_cloud_or_haze_pct` | QA-3 | Same as `cloud_or_haze_pct`, but over the tasked AOI only — preferred when an AOI exists; not available for open-data scenes |
| `cloud_or_haze_pct` | QA-3 | % of the scene's valid footprint flagged cloud **or** haze/smoke in `data_mask.tiff` (union, not sum — a pixel flagged both counts once) |
| `quality_mask_coverage_pct` | QA-2 | % of the scene's valid footprint that also has a value in `pixel_quality_mask.tiff` — below 100% means the quality mask is missing, shifted, or truncated |
| `interpolated_pct` | QA-4 | % of band-pixels (pixels × bands, not just pixels) flagged as interpolated in the pixel quality mask, scene-wide |
| `max_high_value_band_interpolated_pct` | QA-4 | Same idea as `interpolated_pct`, but for the single worst red-edge (711–782nm) band alone — catches a defect concentrated in a few bands that a scene-wide average would dilute |
| `band_corr_mean` | QA-7 | Mean correlation between adjacent spectral bands, scene-wide — low values mean the reflectance data is internally inconsistent |
| `band_corr_min_tile` | QA-7 | Same correlation check, but the worst of an 8×8 grid of spatial tiles — catches a localized inconsistency a scene-wide mean would hide |
| `reflectance_out_of_bounds_pct` | QA-6 | % of valid pixels with reflectance outside the physically valid [0,1] range |
| `geolocation_rmse_px` / `coreg_offset_px` | QA-5 | Geolocation and cross-band co-registration error, in pixels — not published in this catalog, so QA-5 is not-assessable for all three scenes |

---

## 7. Future: LLM-assisted escalation summaries

- Not built — no demo scene escalates yet to validate it against
- Would only summarize an already-decided escalation ticket (§4) for the on-call human, in plain language — never touch the QA-1…QA-7 decision logic itself, which stays mechanical and auditable (§3)
