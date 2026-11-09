# Appendix: method and data detail

This appendix backs the 2-page note. It shows how I cleaned the export, which data gaps I found, and which checks would stop bad data at entry. Use it to audit any number in the note.

## Terms used here

These are definitions I set for this analysis. Every table below uses them.

| Term | Meaning |
| --- | --- |
| Attempt | One processing run of an image. A retry is a new attempt. |
| Uploaded | The image is on DataHub. |
| Delivered | Uploaded **and** QC Result = Pass. An upload without a QC pass is not delivered. |
| Processable | The image was captured, so it can be processed. Never-captured images are excluded. |
| Late | Past the SLA deadline, whether delivered late or still open. |
| On-time % | Images delivered by the deadline ÷ processable images whose deadline has passed. In the workbook: Delivered and Hours vs Deadline ≤ 0. |
| Passed with caveat | QC passed the image but noted an issue: Low SNR, Minor haze or Artifact reduced. |
| Customer status: shown vs derived | Shown is what CS tells the customer. Derived is what the pipeline data says. |
| Snapshot | The latest timestamp in the export, used as "now" because the export has no timestamp of its own. |
| Fixes\_Log | Workbook tab that keeps every original value I changed. |
| Column\_Map | Workbook tab that explains what each column means. |

## How I cleaned the data

Every number in the note depends on these decisions. Source: IPR\_Cleaned\_Data.xlsx.

| Decision | What I did | Why |
| --- | --- | --- |
| One row per image | Kept the latest valid attempt per image and removed stale duplicates. One Row Status column marks each row: Latest attempt, Not captured, Earlier attempt or Removed. Row-to-image counts: [Overview](00_submission.md) | Each image is counted once |
| Priority and SLA | Locked to attempt 1: P0 8h, P1 12h, P2 16h, P3 24h, P4 48h | A retry can change priority (21 images did), which would move the deadline |
| Delivered | QC pass + upload, shown in Delivery Status | An upload without a QC pass isn't a finished delivery (3 images) |
| Processable | 89 of 95 images; the 6 never captured are excluded | An image that was never captured can't be late in processing |
| Conflicts | One Conflicts column with 20 types; None means clean | Shows every problem in a row in one place (81 of 95 images have at least one) |
| Stage times | Used all 123 valid attempts, in 4 duration columns | Retries use pipeline time too, so every attempt counts |
| Snapshot | 2026-06-30 16:05 UTC | The export has no timestamp, so I measure the age of open images from here |
| Labels and timestamps | One value per meaning, one UTC format; originals in Fixes\_Log | Groups and dates are only correct once spellings and formats match |
| Late | Past the SLA deadline; one rule in every view | "Not delivered" would also count images that aren't due yet |
| Passed with caveat | Counts as delivered but is shown separately | A known issue isn't a clean pass, and the team should see it |
| Customer status | Compared shown with derived and ranked mismatches by risk | 45 of 95 differ, so CS needs to know which to fix first |
| Internal customers | Calibration and Internal Demo stay in pipeline metrics and are left out of customer views | They load the pipeline the same way but have no customer to update |
| Last Pipeline Status (raw) | Renamed from Processing Status. Kept but not used for any metric or gate | Every stage writes its last event here, and it lags the timestamps in 41 of 123 attempts |
| QC Finding | Grouped the 15 spellings in Failure Reason into one list: BBR, Processing error: ISOFIT crash, Processing error: Water mask, Input error: Missing metadata, No data, Caveat: Low SNR, Caveat: Minor haze, Caveat: Artifact reduced, None | Every Fail has a reason, so the field is usable once its spellings are merged |
| Offset North / East (km) | Read as the target's offset from the plan, as in Column\_Map | It isn't off-nadir displacement; Off Nadir (°) holds the view tilt |

Breakdown of passes with a caveat:

| Group | With caveat | Total |
| --- | --- | --- |
| Delivered | 24 | 61 |
| On time | 21 | 52 |

Leaving out internal customers barely changes on-time: 58% with them, 59% without.

### Label changes

Each meaning now has one value. The originals are in Fixes\_Log.

| Column | Raw variants | Cleaned values | Rows changed |
| --- | --- | --- | --- |
| Cloud Status | CLEAR, clear, Partial cloud, partly cloudy, Partly Cloudy, CLOUDY | Clear (<30%), Partial (30–70%), Cloudy (>70%), Unknown | 119 |
| Bandset | VNIR\_FULL, Standard\_RGB, vegetation, VEG, RedEdge | VNIR Full, RGB, Vegetation, Red Edge, Water/Coastal | 110 |
| Priority | Urgent, P0, P1, High, high, P2, Standard, blank | P0 (8h), P1 (12h), P2 (16h), P3 (24h), P4 (48h) | 108 |
| QC Result | pass, Pass, QC Pass, Manual pass with note, QC Fail, FAIL\_artifact, Severe / Moderate BBR, NA | Pass, Fail, Pending, Reprocess required, Not applicable | 86 |
| Image Complete | OK, complete, Partial, Strip incomplete | Complete, Incomplete, No image | 86 |
| Reprocessed | no, False, blank | Dropped: Attempt > 1 already says this | 74 |
| Target Status | Missed, NOT\_CAPTURED | Captured, Partial, Not captured | 9 |
| Relative Light | 0.48, 0.72 (numbers in a text field) | Flagged as Unmapped numeric | 6 |
| Strip Fulfillment | fulfilled | Fulfilled | 4 |

**Note on priority:** the raw names don't line up with the new ones. Raw High (16h) becomes P2, and raw P2 (24h) becomes P3.

### Why the columns say QC, not QA

- **QC (quality control)** checks one image: does this image pass or fail review?
- **QA (quality assurance)** checks the process across all images: is the pipeline delivering good images on time? It isn't a review step. It is measured with metrics such as on-time delivery and first-pass QC pass rate, shown on the dashboard.
- The export records only QC, so I renamed the columns to match: QA Assigned → QC Start, Manual QC Status → QC Result.
- "QA/QC" stays as the team name, as in the brief.

## Data gaps: what's missing and how to fix it

81 of 95 images have at least one conflict. The biggest gap is the missing QC end time, which means review time can't be measured. The note groups these 15 gaps into four themes.

| # | Gap | Impact | Fix |
| --- | --- | --- | --- |
| 1 | No QC end time | QC review time can't be measured | Log QC start and end |
| 2 | QC starts after upload in 74% of attempts | QC may not be gating delivery | Open question for IPR / QA (below) |
| 3 | Customer status is wrong for 45 of 95 images | Customers are misinformed | Derive customer status from pipeline state |
| 4 | Missing values: 13 uploads, 8 strip times, 6 QC starts, 4 processing ends, 3 cloud % | Those rows drop out of timing | Make each field required at its handoff |
| 5 | 6 stale duplicate rows | Images counted twice | Unique key: Image ID + attempt |
| 6 | Priority changed on retry for 21 images | An SLA can look met after a downgrade | Lock priority to attempt 1 |
| 7 | Mixed date formats, messy labels, stale status text | Wrong dates and stages | One UTC format and fixed status lists |
| 8 | No export timestamp | Ages depend on an assumed snapshot | Stamp each export |
| 9 | No order-created time | SLA can only be measured from acquisition | Log order time |
| 10 | No per-step processing times; queue names don't show the step | Can't tell which step makes P0 miss by 2.4h | Log L1C / ISOFIT / L2A start and end |
| 11 | No escalation log; 25 of 34 blocked images show no sign of escalation, including all 3 stuck runs | Can't tell whether blocked images reached the right team | Log Escalated At, Escalated To and ticket ID |
| 12 | QC Result not updated: 8 rows still say Pending though Failure Reason already holds a verdict | Images wait for a decision QC may already have made | Record the result and the reason in one step |
| 13 | Rerun after delivery with no reason: 3 images delivered on attempt 1 were re-run, 2 with priority raised | Can't tell a customer request from a QC recheck, and Delivered hides open rework (the customer now sees At risk) | Require a rerun reason when an attempt starts on a delivered image |
| 14 | No SNR or haze % logged; both appear only in QC notes | Can't set thresholds, trend sensor quality or check a caveat | Log SNR per band and haze % per image |
| 15 | Notes have no author; by wording they come from IPR, QA/QC, CS and ground | Notes can't be routed or trusted, and no one owns follow-up | Log the note's author and team |

How the cleaned data handles some of these today:

| Gap | Today |
| --- | --- |
| 6 | The workbook keeps the raw per-attempt deadline as Attempt Deadline (raw); it differs on 24 retry rows |
| 7 | Stale status text in 41 of 123 attempts |
| 12 | Of the 8 Pending rows, Failure Reason reads as a pass in 5 and a fail in 3 |
| 14 | Low SNR is noted on 15 images and Minor haze on 12 |

### Checks that stop bad data at entry

The workbook can only flag problems after the fact. These checks would stop them when the data is written. I don't block "uploaded before QC" in the workbook, because that would hide a signal the team still has to explain.

| Check | Where it runs | Action | Today |
| --- | --- | --- | --- |
| Timestamps in order: acquisition ≤ trigger ≤ processing end ≤ QC start | Pipeline write | Reject and alert | |
| Upload only after QC Result = Pass | DataHub upload step | Block, once the team confirms QC gates delivery | 74% of attempts start QC after upload |
| One row per Image ID + attempt | Export / database key | Reject the duplicate | 6 duplicates |
| Priority and SLA locked after attempt 1 | Order system | Allow a change only with an override and a reason | 21 images changed |
| Status values from a fixed list | Every status field | Reject free text | |
| Cloud % between 0 and 100; angles in range | Ingest | Reject and flag | |
| Customer status derived from pipeline state | CS tool | Never set by hand | 45 of 95 wrong |
| Target Status from Plan Coverage %: ≥ 95% = Captured, 1–94% = Partial, 0% = Not captured | Acquisition / ingest | Set automatically, never by hand | Some "Not captured" images show 12.4% coverage |
| Image Complete means data integrity only: "All frames received: Yes / No" | Ingest | Keep coverage out of this field, so it can't contradict Target Status | 8 rows say Complete at 42–79% coverage |
| Completeness gate before processing | Ingest, before Trigger | All frames → process. AOI frames present → process, flagged. AOI frames missing → hold, then re-downlink or re-task; never rerun | 20 of 23 incomplete attempts were processed |
| QC Result holds the decision only (Pass, Fail, Pending, Reprocess required); the defect and its severity go in QC Finding (e.g. BBR: severe / moderate) | The system behind Manual QC Status | Required on every Fail and every pass with a caveat | Severity sits in free text; the workbook rebuilds it as BBR Severity |

Why the completeness gate matters:

| Images | Failed QC | Total |
| --- | --- | --- |
| Incomplete | 7 | 14 |
| Complete | 3 | 75 |

The full set has 20 column-pair rules. Each shows how often this export breaks it and whether to block, warn or review: see "Contradiction checks" in the [IPR Data Cleaning Rules](https://claude.ai/artifact/55PXGiyx3VkYovwm47s61s).

## Open questions for the team

- **Does QC have to pass before upload?** QC starts after upload in 74% of attempts. Until IPR / QA confirm, I flag this but don't block it.
- **Who sets Strip Fulfillment, and when?** It's set after upload in 44 of 53 rows, and 5 never-captured images are marked Fulfilled. I left it out of all metrics.
- **Moderate or severe BBR?** One row says moderate in its QC status but severe in Failure Reason. I recorded it as Severe in the workbook's BBR Severity column.
