# Appendix: method and data detail

Not part of the two pages. The cleaning decisions, label mappings, full list of data gaps and the checks to enforce at the source, kept here as the audit trail behind the note.

## How I cleaned the data

Every number depends on these decisions. Source: IPR\_Cleaned\_Data.xlsx. Terms are in the Glossary of the rules doc.

| Decision | What I did | Why |
| --- | --- | --- |
| One row per image | Latest valid attempt per image; stale duplicates removed. Counts from export rows to images: [Overview](00_submission.md). One Row Status column marks each row (Latest attempt / Not captured / Earlier attempt / Removed), replacing two Yes/No flags | No double counting |
| Priority and SLA | Locked to attempt 1: P0 8h, P1 12h, P2 16h, P3 24h, P4 48h | 21 images changed priority on a retry |
| Delivered | QC pass + upload (Delivery Status) | 3 images uploaded without a QC pass don't count |
| Processable | 89 of 95; the 6 never captured are excluded | Partly cloudy images were still delivered (up to 68% cloud) |
| Conflicts | One column, 20 types; None = clean | 81 of 95 images have at least one |
| Stage times | All 123 valid attempts; 4 duration columns | Every run costs time |
| Snapshot | 2026-06-30 16:05 UTC, the latest timestamp | Ages undelivered images |
| Labels and timestamps | Standardized; originals in Fixes\_Log | Audit trail |
| Late | Past the SLA deadline (delivered late or still open); one rule across every view | "Not delivered" would count images not yet due |
| Passed with caveat (Low SNR / Minor haze / Artifact reduced) | Counts as delivered, shown apart: 24 of 61 delivered, 21 of 52 on time | Ambiguous success label; a known issue isn't a clean pass |
| Customer status | Shown vs derived, ranked by risk: 4 shown Delivered when not, 2 delays hidden | 45 of 95 differ; CS must fix the worst first |
| Internal customers | Calibration and Internal Demo stay in pipeline metrics; left out of customer views | Same pipeline load, but no customer to update; on-time barely moves (58% → 59%) |
| Processing Status → Last Pipeline Status (raw) | Renamed, kept raw and treated as unreliable: not used for any metric or gate | Not a processing status: every stage writes its last event here (QC 15, delivery 40 attempts). Lags the timestamps in 41 of 123 attempts |
| Failure Reason | Kept raw; 15 spellings grouped into QC Finding (BBR, Processing error: ISOFIT crash, Processing error: Water mask, Input error: Missing metadata, No data, Caveat: Low SNR, Caveat: Minor haze, Caveat: Artifact reduced, None) | Free text with five spellings of BBR; every Fail has a reason, so it's usable once grouped |
| Offset North / East (km) | Read as target offset from plan, per Column\_Map | Not off-nadir ground displacement; view tilt is Off Nadir (°) |

### Text changes

One value per meaning; originals in Fixes\_Log.

| Column | Raw variants | Cleaned values | Rows changed |
| --- | --- | --- | --- |
| Cloud Status | CLEAR, clear, Partial cloud, partly cloudy, Partly Cloudy, CLOUDY | Clear (<30%), Partial (30–70%), Cloudy (>70%), Unknown | 119 |
| Bandset | VNIR\_FULL, Standard\_RGB, vegetation, VEG, RedEdge | VNIR Full, RGB, Vegetation, Red Edge, Water/Coastal | 110 |
| Priority | Urgent, P0, P1, High, high, P2, Standard, blank | P0 (8h), P1 (12h), P2 (16h), P3 (24h), P4 (48h) | 108 |
| QC Result | pass, Pass, QC Pass, Manual pass with note, QC Fail, FAIL\_artifact, Severe / Moderate BBR, NA | Pass, Fail, Pending, Reprocess required, Not applicable | 86 |
| Image Complete | OK, complete, Partial, Strip incomplete | Complete, Incomplete, No image | 86 |
| Reprocessed | no, False, blank | Column dropped: Attempt > 1 says the same | 74 |
| Target Status | Missed, NOT\_CAPTURED | Captured, Partial, Not captured | 9 |
| Relative Light | 0.48, 0.72 (numbers in a text field) | Flagged as Unmapped numeric | 6 |
| Strip Fulfillment | fulfilled | Fulfilled | 4 |

Watch the priority names: raw High (16h) → P2, raw P2 (24h) → P3.

### QC vs QA, and why the columns say QC

- **QC** = review of each image. **QA** = process quality, shown as metrics.
- The data only records QC, so the columns say QC: QA Assigned → QC Start, Manual QC Status → QC Result.
- "QA/QC" stays as the team name, as in the brief.

On-time % = delivered by the deadline ÷ processable images past their deadline (all 89). In the workbook: Delivered and Hours vs Deadline ≤ 0.

## All 15 data gaps

81 of 95 images have a conflict. Biggest gap: no QC-end time, so review can't be timed. The main note groups these into four themes.

| # | Gap | Impact | Fix |
| --- | --- | --- | --- |
| 1 | No QC-end time | QC review can't be timed | Log QC start and end |
| 2 | QC starts after upload (74% of attempts) | QC may not gate delivery | Confirm with IPR / QA |
| 3 | Customer status wrong for 45 of 95 images | Customers misinformed | Derive it from pipeline state |
| 4 | Missing values (13 uploads, 8 strip times, 6 QC starts, 4 processing ends, 3 cloud %) | Rows drop out of timing | Required at each handoff |
| 5 | 6 stale duplicate rows | Double counting | Unique key: Image ID + attempt |
| 6 | Priority changed on retry (21 images) | SLA can look met after a downgrade | Lock priority to attempt 1; the workbook keeps the raw per-attempt deadline as Attempt Deadline (raw) (differs on 24 retry rows) |
| 7 | Mixed formats, messy labels, stale status text (41 of 123 attempts) | Wrong dates and stages | One UTC format, fixed status lists |
| 8 | No export timestamp | Ages rest on an assumed snapshot | Stamp each export |
| 9 | No order-created time | SLA only measurable from acquisition | Log order time |
| 10 | No per-step processing times; queue names don't show the step | Can't tell which step makes P0 miss 2.4h | Log L1C / ISOFIT / L2A start and end |
| 11 | No escalation log; 25 of 34 blocked images show no sign of escalation (all 3 stuck runs) | Can't tell if blocked images reached the right team | Log Escalated At, Escalated To and ticket ID |
| 12 | QC Result not updated: 8 rows still Pending though Failure Reason already holds a verdict (5 read as a pass, 3 as a fail) | Images wait for a decision QC may already have made | Record the result and the reason in one step, where QC records its result |
| 13 | Rerun after delivery with no reason: 3 images delivered on attempt 1, then re-run (2 with priority raised); the customer now sees At risk | Can't tell a customer request from a QC recheck; Delivered hides open rework | Require a rerun reason when an attempt starts on a delivered image |
| 14 | No SNR or haze % logged; both exist only as QC notes (Low SNR 15 images, Minor haze 12) | Can't set thresholds or trend sensor quality; a caveat can't be checked | Log SNR per band and haze % per image |
| 15 | Notes have no author; by wording they come from IPR, QA/QC, CS and ground | A note can't be routed or trusted; no one owns follow-up | Log the note's author and team |

### Checks to enforce at the source

The sheet only flags problems. These checks stop them at the source. (Blocking "uploaded before QC" in the sheet would hide a signal the team still has to explain.)

| Check | Where it runs | Action |
| --- | --- | --- |
| Timestamps in order: acquisition ≤ trigger ≤ processing end ≤ QC start | Pipeline write | Reject and alert |
| Upload only after QC Result = Pass | DataHub upload step | Block, once the team confirms QC gates delivery |
| One row per Image ID + attempt | Export / database key | Reject the duplicate |
| Priority and SLA locked after attempt 1 | Order system | Changes need an override with a reason |
| Status values from a fixed list | Every status field | Reject free text |
| Cloud % between 0 and 100, angles in range | Ingest | Reject and flag |
| Customer status derived from pipeline state | CS tool | Never set by hand |
| Target Status derived from Plan Coverage %: ≥ 95% = Captured, 1–94% = Partial, 0% = Not captured | Acquisition / ingest | Set automatically, never by hand. Removes "Not captured" images that show 12.4% coverage |
| Image Complete limited to data integrity: "All frames received: Yes / No" | Ingest | Says nothing about coverage, so it can't contradict Target Status (8 rows say Complete at 42–79% coverage today) |
| Completeness gate before processing: all frames received, or the AOI's frames are | Ingest, before Trigger | Complete → process. AOI frames present → process, flagged. AOI frames missing → hold, re-downlink or re-task; never rerun. Today 20 of 23 incomplete attempts were processed, and 7 of 14 incomplete images failed QC (vs 3 of 75 complete) |
| QC Result is the decision only (Pass, Fail, Pending, Reprocess required); the defect goes in QC Finding with a severity (e.g. BBR: severe / moderate) | Where QC records its result (the system behind Manual QC Status) | Required on every Fail and every pass with a caveat. Today severity sits in free text; the workbook rebuilds it as BBR Severity |

The full set is 20 column-pair rules, each with how often this export breaks it and whether to block, warn or review: see "Contradiction checks" in the [IPR Data Cleaning Rules](https://claude.ai/artifact/55PXGiyx3VkYovwm47s61s).

## Further open questions

- **Who sets Strip Fulfillment, and when?** It comes after upload in 44 of 53 rows, and 5 never-captured images are marked Fulfilled. Left out of all metrics.
- **Moderate vs severe BBR:** one row says moderate in its QC status but severe in Failure Reason; I recorded it as Severe. BBR Severity in the workbook keeps which.
