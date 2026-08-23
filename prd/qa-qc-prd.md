# QA/QC PRD — Hyperspectral Image Pipeline Monitoring

**Owner:** Image Product Manager (pipeline monitoring layer)
**Scope:** This PRD governs QA/QC, failure categorization, retry/escalation, versioning, and delivery-readiness for hyperspectral image products moving through the pipeline, from raw capture (L0/L1B) to delivered product (L2A+).

**Explicitly out of scope:** the image-processing algorithms themselves (radiometric calibration, atmospheric correction, orthorectification, band co-registration). This PRD defines what "good" and "bad" output looks like and what the pipeline does in response — not how the processing algorithms work internally.

---

## 1. Processing levels in scope

| Level | Description | QA applies? |
|---|---|---|
| L0 | Raw sensor telemetry, unprocessed | No — QA starts at L1B |
| L1B | Radiometrically calibrated, geolocated, not atmospherically corrected | Yes — structural/sensor QA |
| L2A | Atmospherically corrected, surface reflectance, analysis-ready | Yes — full QA, this is the delivery product |

Every rule below states which level(s) it applies to.

---

## 2. Failure categories

Every QA failure must be assigned exactly one primary category. Categories are mutually exclusive by definition (a scene can have multiple failures, but each failure event gets one category).

| Code | Category | Definition | Typical L level detected |
|---|---|---|---|
| `CLOUD` | Cloud/atmospheric obstruction | Cloud, haze, or smoke mask coverage exceeds usable threshold | L1B, L2A |
| `SENSOR` | Sensor artifact | Striping, dead pixels, band dropout, saturation clipping | L1B |
| `GEOM` | Geometric misalignment | Geolocation offset or band co-registration error exceeds tolerance | L1B, L2A |
| `RADIO` | Radiometric anomaly | Reflectance values outside physically plausible range for the surface type; internally inconsistent band ratios | L2A |
| `MASK_GAP` | Missing/incomplete quality mask | Quality or cloud mask absent, malformed, or covers less than the full scene extent | L1B, L2A |
| `INCOMPLETE` | Incomplete data | Fewer than the expected 23 bands present, or scene extent smaller than tasked AOI | L1B |

A scene with **no** failures across all categories is `CLEAN`.

---

## 3. QA pass/fail rules

Rules are evaluated in order. First matching rule determines the outcome for that scene. All thresholds are placeholders to be tuned against real Wyvern data in step 2/3 of this project — the point here is that every rule is a **mechanical, executable condition**, not a judgment call.

| Rule ID | Level | Condition | Category if failed | Outcome |
|---|---|---|---|---|
| QA-1 | L1B | Band count < 23 or scene coverage < 95% of tasked AOI | `INCOMPLETE` | **Escalate** |
| QA-2 | L1B/L2A | Quality mask missing, unparseable, or covers < 100% of scene extent | `MASK_GAP` | **Escalate** |
| QA-3 | L1B/L2A | Cloud/haze/smoke mask coverage > 40% of scene | `CLOUD` | **Retry** (re-task if coverage > 80%, see §4) |
| QA-4 | L1B | Dead/saturated pixel count > 2% of total pixels, or any full-band dropout | `SENSOR` | **Escalate** |
| QA-5 | L1B/L2A | Geolocation RMSE > 1 pixel, or cross-band co-registration offset > 0.5 pixel | `GEOM` | **Retry** |
| QA-6 | L2A | Reflectance values outside [0, 1] physical bounds for > 0.5% of valid pixels (excluding masked pixels) | `RADIO` | **Retry** |
| QA-7 | L2A | Reflectance internally inconsistent — e.g. NIR/Red ratio implies vegetation where cloud mask says clear sky, or band-to-band correlation falls outside expected range for the scene's land-cover class | `RADIO` | **Escalate** (flag-for-review, not auto-fixable by reprocessing — don't silently trust output that contradicts its own inputs/metadata) |
| — | — | No rule above fired | `CLEAN` | **Pass** |

**Design note:** rules that describe a fixable, mechanical problem (bad geolocation, bad atmospheric correction, transient cloud cover) route to **retry** — the processing pipeline re-runs, possibly with adjusted parameters. Rules that describe a problem reprocessing can't fix (missing bands, dead sensor pixels, an anomaly that contradicts its own metadata) route to **escalate** — a human has to look at it.

---

## 4. Retry vs. escalate logic

### Retry conditions
A scene routes to **retry** when:
- The failure category is `CLOUD`, `GEOM`, or `RADIO`, **and**
- Retry count for this scene < `MAX_RETRIES` (default: 2), **and**
- The failure is plausibly transient or parameter-fixable (e.g. cloud cover from a bad tasking window, geometric offset fixable by re-running co-registration with different tie points)

On retry: increment retry count, log the triggering rule, re-run the affected processing stage (not necessarily the whole pipeline — e.g. a `GEOM` failure only needs orthorectification re-run, not radiometric calibration).

### Escalate conditions
A scene routes to **escalate** when:
- The failure category is `INCOMPLETE`, `SENSOR`, or `MASK_GAP` (structural problems reprocessing cannot fix), **or**
- Retry count has reached `MAX_RETRIES` and the scene still fails, **or**
- QA-7 fires (internally inconsistent output — needs human judgment, not another automated pass)

On escalate: create a ticket with the scene ID, failure category, rule that fired, and full reasoning trace. Assign to on-call Image PM / pipeline engineer. Scene is held at its current version, not delivered, until manually cleared.

### Auto-retry ceiling
If `MAX_RETRIES` is reached, the system **must** escalate rather than retry indefinitely. Silent infinite retry is treated as a pipeline bug, not acceptable behavior.

---

## 5. Versioning rules

- **New version** (`v1` → `v2`) is created when: the *inputs* to processing change — reprocessing with different parameters after a retry, a corrected quality mask, or reprocessing triggered by an escalation resolution.
- **Same version, new attempt** is used when: an automated retry re-runs the *same* parameters (e.g. transient failure, infra retry) and produces a materially identical result.
- Every version is immutable once marked `delivered` — a delivered product is never silently overwritten. A correction after delivery always produces a new version and a delivery notice to the customer.
- Version history retains the QA outcome, failure category (if any), and reasoning trace for every version — not just the final passing one. This is what makes the pipeline auditable.

---

## 6. Delivery-ready definition

A scene is **delivery ready** if and only if:
1. It reached `CLEAN` status (no rule in §3 fired), **and**
2. It is at L2A, **and**
3. Its quality mask is present and covers 100% of scene extent, **and**
4. It has not been superseded by a newer version of the same acquisition

A scene that is `CLEAN` but still under a pending escalation review from an *earlier* version is **not** delivery ready until that escalation is resolved and the current version independently passes QA.

"Delivery ready" is a pipeline-monitoring determination, not a processing-algorithm determination — the algorithms produce output, this layer decides whether that output is fit to ship.

---

## 7. What this PRD deliberately leaves as placeholders

Thresholds (40% cloud coverage, 2% dead pixels, 1-pixel geolocation RMSE, etc.) are reasonable starting points based on common hyperspectral QA practice, not values pulled from Pixxel's actual production system. Step 2/3 of this project (pulling real Wyvern scenes and walking through their actual quality masks) is what validates or adjusts these numbers against real data — that's the point of using real imagery instead of writing this PRD in the abstract.
