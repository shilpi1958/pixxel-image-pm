# IPR Data Cleaning Rules

Nov 5, 2026 · @Sj

Rules used to build IPR\_Cleaned\_Data.xlsx. Raw values are never overwritten; originals are in Fixes\_Log.

## Rule 1: Same-attempt duplicates

One row per Image ID + attempt. 6 stale duplicates removed. Counts from export rows to images: [Overview](00_submission.md).

1. Keep the most final status: Delivered/Uploaded > Passed/Done > QC pending > Reprocessing. A terminal outcome (Target missed, No data) beats an in-progress one.
2. Tie → more timestamps filled, then the latest.
3. Notes only confirm a pick; they never decide.

| Image ID | Kept (Excel row) | Dropped | Decided by |
| --- | --- | --- | --- |
| FF02\_20260607\_1028\_MADHY | 25 · DataHub upload complete | 27 · Reprocessing | Status rank |
| FF01\_20260608\_1029\_SAHAR | 29 · L2A Passed | 32 · Reprocessing | Status rank |
| FF01\_20260611\_1067\_PUNJA | 44 · Done | 45 · Manual QC pending | Status rank |
| FF03\_20260624\_1047\_ODISH | 104 · Done | 105 · Reprocessing | Status rank |
| FF01\_20260623\_1026\_NILED | 132 · Target missed | 137 · Manual QC pending | Terminal outcome |
| FF03\_20260625\_1074\_GUJAR | 133 · No data | 136 · No data | Tie → stale note |

## Rule 2: Latest valid attempt per image

One row per image. 27 images had 2–3 attempts (26 processable + 1 never captured).

1. Latest = highest attempt that was actually triggered.
2. No valid attempt → Row Status = Not captured.
3. SLA is locked to attempt 1: priority, SLA hours, deadline. The clock starts at acquisition, which is the same on every attempt (assumed: SLA runs from acquisition, not order).

   The raw per-attempt deadline is kept beside it as Attempt Deadline (raw): acquisition + this attempt's SLA hours. It differs from SLA Deadline on 24 retry rows where priority changed. Not used for metrics; it is the evidence that a retry can move the deadline.
4. Delivered time = earliest QC-passed upload across attempts.
5. Earlier attempts stay as history (italic grey): out of image KPIs, used for attempt metrics.

| Edge case | Images | Handling |
| --- | --- | --- |
| Attempt number vs trigger order disagree | 2 | Keep highest attempt; in Conflicts |
| Delivered earlier, newer attempt not uploaded | 3 | Counts as delivered; in Conflicts. Rework of the same capture, not a new order |
| Priority changed between attempts | 21 | Use attempt 1; in Conflicts |
| No attempt ever triggered | 3 | Not processable |

### Why 89 vs 95

6 of 95 images were never captured (Row Status = Not captured). They count as images but stay out of pipeline KPIs, which use the 89 latest attempts.

- Not-captured images feed a capture-rate metric, never hidden.
- Cloud didn't cause misses: 5 of 6 misses had 21–40% cloud.
- Partial captures and partial cloud stay in; split them with Target Status and Cloud Status.
- Future rule: a capture with >70% cloud would be not processable. No image in this data hits it.

## Rule 3: Timestamps

One UTC format. Missing times are flagged, never filled. Snapshot: 2026-06-30 16:05 UTC.

1. Three formats parsed; day-first confirmed against the Image ID date.
2. Expected order: acquisition → trigger → processing end → QC start.

| Check | Rows / images | Handling |
| --- | --- | --- |
| Mixed formats | 9 rows | Converted |
| Triggered, no end time | 4 | Stuck; statuses say otherwise (in Conflicts) |
| Processed, no QC start | 6 | Already passed QC: start time missing |
| Uploaded before QC start | 55 of 74 attempts | Open question. Staging ruled out (no QC fail was uploaded) |
| Deadline = acquisition + SLA | 92 of 92 | Consistent |

## Rule 4: Labels

One value per meaning; unseen labels → "Unmapped", never guessed. Last Pipeline Status (raw) stays raw text: it is stale in 41 of 123 attempts.

| Column | Clean values | Notes |
| --- | --- | --- |
| Bandset | VNIR Full, RGB, Vegetation, Water/Coastal, Red Edge | 4 spellings of Vegetation merged |
| Cloud Status | Clear, Partial, Cloudy, Unknown | <30%, 30–70%, >70% |
| Target Status | Captured, Partial, Not captured | Missed + NOT\_CAPTURED merged |
| QC Result | Pass, Fail, Pending, Reprocess required, Not applicable | Pass with note = Pass; BBR / FAIL\_artifact = Fail. \
Moderate BBR (2 rows) assumed Fail, to confirm with QA. \
\
BBR is a finding, not a status; severity is kept in BBR Severity (Severe / Moderate / Unspecified / None; 13 \
\
BBR attempts: 10 severe, 1 moderate, 2 unspecified). \
\
At the source it should be recorded where QC records its result (the system behind Manual QC Status) |
| Image Complete | Complete, Incomplete, No image | OK = Complete |
| QC Finding | BBR, Processing error: ISOFIT crash, \
Processing error: Water mask, \
Input error: Missing metadata, No data, \
Caveat: Low SNR, \
Caveat: Minor haze, \
Caveat: Artifact reduced, None | Caveat: X = passed with that note |
| Priority | P0 8h, P1 12h, P2 16h, P3 24h, P4 48h | Ordered by SLA: High → P2, raw P2 → P3 |
| Strip Fulfillment | Fulfilled, Partially, Not fulfilled, Unknown | fulfilled merged |

### Last Pipeline Status: kept raw, treated as unreliable

Last Pipeline Status (raw) keeps all 17 raw values unchanged. It is **not used for any metric, gate or status**. Where an image is comes from timestamps, QC Result and Stuck instead.

Renamed from Processing Status: it is the last status any stage wrote, not a processing status. Delivery wrote 40 attempts, processing 35, QC 15 and pre-processing 7; 33 say only Done or Complete. Fix at source: each stage owns its own status, and the current stage is derived.

Why: one field mixes five stages, and it often lags behind the timestamps.

| Stage the text claims | Raw values (rows) |
| --- | --- |
| Acquisition | No data (6), Target missed (1), Not triggered (1) |
| Processing, in progress or stuck | Reprocessing (7), Stuck in queue (2) |
| Processing outcome | L2A Passed (18), L2A Failed (7), Failed at L2A (2), Failed at L1C (1), ISOFIT failed (1) |
| QC | Manual QC pending (12), Needs science review (3), QC Hold (2) |
| Delivery | DataHub upload complete (21), Sent to Aurora (19) |
| Unclear stage | Done (24), Complete (9) |

Where it disagrees with the other fields (valid attempts):

| Status text says | But | Attempts |
| --- | --- | --- |
| Manual QC pending | QC Result = Pass | 10 |
| Done / Complete / L2A Passed | QC still Pending | 8 |
| DataHub upload complete | QC still Pending (uploaded without a pass) | 2 |
| L2A Passed / Complete / Sent to Aurora | No Processing End (stuck) | 3 |
| Stuck in queue | Processing finished | 2 |

The only use left is a weak escalation hint (Needs science review, QC Hold, Reprocessing). Fix at the source: one status per stage, from a fixed list, set automatically by each system.

### Failure Reason: kept raw, grouped into QC Finding

Failure Reason (raw) keeps all 16 raw values (blank included) unchanged. It is **usable once grouped**: QC Finding groups it into 5 values, and that is what the metrics use. Every Fail and Reprocess required has a reason.

| QC Finding | Raw values (rows) | Total |
| --- | --- | --- |
| Caveat: Low SNR | low SNR but accepted (19) | 19 |
| Caveat: Minor haze | minor haze (16) | 16 |
| Caveat: Artifact reduced | artifact reduced (5) | 5 |
| BBR | severe BBR (4), bbr severe (4), BBR (2), Bright banding (2), Banding bright (1) | 13 |
| Processing error: ISOFIT crash | ISOFIT crash (3) | 3 |
| Processing error: Water mask | water mask failed (3) | 3 |
| Input error: Missing metadata | missing metadata (2) | 2 |
| No data | No frames (4), Target not captured (2), black frame (1) | 7 |
| None | blank (64), Recovered after reprocess (4) | 68 |

Caveats are split by type so each can be filtered (15 / 12 / 5 images). Low SNR and haze are notes only: no measured SNR or haze % is logged. Ask Engineering to log SNR per band and haze % per image; until then no SNR column.

Processing errors are split by step and owner. \
ISOFIT crash and water mask are L2A steps (science team). \
Missing metadata is an input error: auxiliary files never arrived, so a rerun alone won't fix it (ground segment / ingest).

What to watch:

- **Free text, five spellings of BBR.** Grouping fixes this; severity is kept in BBR Severity. All 13 BBR rows agree with QC Result and BBR Severity except one (moderate in QC status, severe in the reason; flagged in Conflicts). BBR repeats on retry: 3 images had it on every attempt.
- **Not all values are reasons.** "Recovered after reprocess" is an outcome, so it counts as a clean pass (the reprocess already shows in Attempt); on 2 rows it sits on attempt 1, flagged in Conflicts. "Target not captured" belongs to acquisition.
- **8 rows are still QC Pending though the reason already reads as a verdict** (5 as a pass, 3 as a fail). These are flagged in Conflicts.
- **Blank means no issue noted,** not a missing value: 64 rows, almost all Pass or Pending.

Fix at the source: pick the finding and its severity from a fixed list, with free text only as a note.

## Rule 5: Numbers

Real number or blank. Impossible values → blank + Conflicts. Text pairs split into two columns.

| Column | Found | Handling |
| --- | --- | --- |
| Cloud Cover % | −4 (1 row), "NA" (2) | Blank + Conflicts |
| Coverage vs Image Complete | 8 rows Complete at 42–79% (all Partial) | Conflicts; trust coverage |
| Coverage vs Target Status | 2 Not captured at 12.4% | Conflicts |
| Relative Light | 0.48, 0.72 among categories | Unmapped numeric; scale unknown |
| Satellite zenith | −0.6° (1 row) | Conflicts; likely sign error |
| Angle and offset pairs | Text pairs | Split |

## Rule 6: Delivered

Delivered = an attempt passed QC and was uploaded. 61 of 89; 52 on time (Hours vs Deadline ≤ 0).

| Delivery Status | Images |
| --- | --- |
| Delivered | 61 (52 on time, 9 late) |
| Failed | 11 |
| QC passed, not uploaded | 7 |
| In progress | 7 |
| Uploaded without QC pass | 3 |
| Not processable | 6 |

Customer status is derived, not taken from the raw column: Delivered / Delayed (late) / At risk (<25% SLA left) / On track / Not captured. At the snapshot all 28 undelivered images are Delayed; customers see only 6 as Delayed.

How the dashboard reads these:

- **Late** = processable, not delivered, past the SLA deadline. Open images not yet due are not late. (At the snapshot all 28 open images are late.) At risk on the dashboard = not late yet, but the upper ETA (p80) lands after the deadline; the workbook's Customer Status (derived) uses < 25% of SLA left instead. Both give 0 at the snapshot.
- **Passes with a caveat (Low SNR, Minor haze, Artifact reduced)** counts as Delivered but is shown apart: 24 of 61 delivered (39%), and 21 of the 52 on-time deliveries. A clean pass and a pass with a known issue are not the same success.
- **Customer status shown wrong** (45 of 95) is ranked by risk: 4 shown Delivered when not, 2 delays hidden, 2 with the wrong delay reason, 37 understated (delivered but not shown so).
- **Failed with BBR** is never told "being reprocessed": none of the 8 BBR images recovered on a retry, so the customer hears "under quality review; we will confirm a new date".
- **Internal customers** (Calibration, Internal Demo: 15 of 95 images) use the same pipeline, so they stay in pipeline, QC and Engineering metrics and the Top 5, but are left out of customer views (late by customer, work complete by customer, Customer Success). Leaving them out barely moves the headline: on-time 58% → 59%, late images 28 → 23.

## Missing data

Only unexplained blanks are gaps (26 of 130 attempt rows). Gaps are never filled.

| Gap | Rows |
| --- | --- |
| Upload missing after QC pass | 13 |
| Strip fulfillment time missing | 8 |
| QC start missing after processing | 6 |
| Processing end missing (stuck) | 4 |
| Cloud % blank or invalid | 3 |
| SNR not in export (Low SNR is only a note, 15 images) | All |
| Haze % not in export (Minor haze is only a note, 12 images) | All |
| Note author not in export (Notes owner unknown) | All |

## Rule 7: Naming

- **QC** = per-image review; **QA** = process quality (metrics only).
- Renamed: QA Assigned → QC Start (assumed; may be a post-upload QA audit), Manual QC Status → QC Result, Image Priority / Deadline → SLA Priority / Deadline, Failure Category → QC Finding.
- **Upload** = sent to DataHub (DataHub Upload); **Delivered** = passed QC and uploaded. "Release" is not used. Column_Map wording for QC Start and DataHub Upload updated to match.
- "Attempt …" = this run; "SLA …" = locked attempt-1 value; "(raw)" = original text; all times UTC; units in the name.

## Rule 8: Conflicts

One column lists every contradiction on a row; None = clean. 81 of 95 images have one, 49 have two or more. 20 types (full list in Column\_Map), e.g. customer status vs data (45), uploaded before QC (42), priority changed (21). Four compare QC Result with the notes: QC Pending while Failure Reason already holds a verdict (8 rows: 5 read as a pass, 3 as a fail), Pass while the status text says QC pending or reprocessing (11), Pass while a note flags recurring BBR (7), and a QC decision on a run that never finished (1). One more: QC status says moderate BBR while Failure Reason says severe (1 row; recorded as Severe), and Failure Reason saying recovered after reprocess on an attempt-1 row (2).

### Contradiction checks: which column can contradict which

Each row is a rule that must hold between two columns, how often this export breaks it, and what an automated check should do. **Block** = reject at write time; **Warn** = allow, but flag for the owner; **Review** = a person decides.

| Stage | Column A | Column B | Must hold | Broken now | Check |
| --- | --- | --- | --- | --- | --- |
| Order | Attempt Priority (attempt 1) | Attempt Priority (later attempts) | Priority doesn't change on a retry without an override | 21 images | Block, override with reason |
| Order | SLA Deadline | Acquisition Time + SLA hours | Equal | 0 of 92 | Block |
| Order | Attempt | Trigger (UTC) | A higher attempt triggers later | 2 | Block |
| Order | Trigger (attempt n+1) | Processing End (attempt n) | The next run starts after the previous one ends | 7 | Warn |
| Acquisition | Cloud Cover % | Cloud Status | < 30% Clear, 30–70% Partial, > 70% Cloudy | 0 | Set automatically |
| Acquisition | Plan Coverage % | Target Status | ≥ 95% Captured, 1–94% Partial, 0% Not captured | 2 | Set automatically |
| Acquisition | Plan Coverage % | Image Complete | Complete only with full coverage | 8 | Block |
| Acquisition | Target Status | Strip Fulfillment | Not captured can't be Fulfilled | 5 | Block |
| Processing | Processing End | Last Pipeline Status | No "passed / complete / sent" without an end; no "stuck" with one | 6 | Status set automatically |
| Processing | Processing End | QC Result | A QC decision needs a finished run | 1 | Block |
| QC | QC Result | Last Pipeline Status | A QC pass can't still read "QC pending" or "Reprocessing" | 11 | Status set automatically |
| QC | QC Result | Failure Reason | Pending has no verdict; every Fail has a reason | 8 / 0 | Block |
| QC | QC Result (raw) | BBR Severity | The severity in the status and in the reason agree | 1 | Block |
| QC | Failure Reason | Attempt | "Recovered after reprocess" only on attempt 2+ | 2 | Block |
| QC | QC Result | Notes | A pass with a "recurring BBR" note gets a second look | 7 | Review |
| QC | QC Start | DataHub Upload | Upload only after QC starts | 55 of 74 attempts | Warn, then Block |
| Delivery | QC Result | DataHub Upload | Upload only after a pass | 3 images | Block (with a P0 override) |
| Delivery | Delivered (earlier attempt) | Later attempt | A rerun after delivery has a recorded reason, and is uploaded or closed | 3 | Warn |
| Delivery | Strip Fulfillment Time | DataHub Upload | Rule unclear: fulfillment comes after upload in 44 of 53 | — | Open question |
| Customer | Customer Status (shown) | Customer Status (derived) | Equal | 45 | Shown status set from derived |

Single-column checks, for the same check job: Cloud Cover % between 0 and 100 (3 broken), Relative Light from its category list (6 numbers), Satellite zenith ≥ 0° (1).

Run the checks where the data is written, not only in this sheet. The sheet flags; the source should block.

## Workbook layout

52 columns: 35 raw (all raw columns covered) + 17 added. Every added column is filled on every row; only raw columns can be blank. One Row Status column says which rows count (it replaced the Image Row and In Pipeline KPI flags, which it fully determined).

| Tab | Holds |
| --- | --- |
| Cleaned\_Data | 136 rows; row 1 = stage, row 2 = headers |
| Column\_Map | Each column: stage, data type, origin, affects (quality / time / both), owner, set by (auto / manual / derived), empty rows, meaning, open question (17 columns) |
| Guide | Colour key, naming |
| Fixes\_Log | Original value of every changed cell (570 rows): labels, timestamps, 3 invalid Cloud % blanked (NA, NA, −4), 24 deadlines recalculated to the attempt-1 SLA, 6 blank deadlines labelled N/A |

**Step timing**

| Step | Start → End | Column | Target | Avg |
| --- | --- | --- | --- | --- |
| 1. Ingest | Acquisition → Trigger | Ingest Wait (h) | 20% | 9.1h |
| 2. Processing | Trigger → Processing End | Processing (h) | 30% | 5.2h |
| 3. QC wait | Processing End → QC Start | QC Wait (h) | 10% | 3.5h |
| 4. QC review + upload | QC Start → QC End (missing) | Not measurable | 25% |  |
| End-to-end | Acquisition → Delivered | End-to-end (h) | 85% | 13.1h |

**Dropped as duplicates:** Delivered, Segment, Processability, Image/Attempt SLA hours, On Time + Hours Late (→ Hours vs Deadline), Reprocessed, Attempt Count, Awaiting QC, Re-delivery In Progress, Hours Stuck, Rework Wait, Failed Stage, Pipeline Step, 5 mismatch flags (→ Conflicts), Label/Timestamp Fixes (→ Fixes\_Log).

**Tagged unreliable (kept raw, not used for metrics):** Customer Status (shown), Last Pipeline Status (raw), Notes, Strip Fulfillment and its time. Red italic header in the data tab; Column\_Map → Unreliable = Yes. Kept because they are the evidence for the gaps they show.

## Glossary

| Term | Meaning |
| --- | --- |
| AOI | Customer's target area |
| Attempt | One processing run; >1 = reprocess |
| Bandset | Spectral bands delivered (RGB, VNIR Full, Vegetation, Red Edge, Water/Coastal) |
| BBR | Bright-banding artifact; top QC failure |
| Conflict | Two fields on a row that contradict |
| DataHub | Upload platform; delivery after QC pass |
| Downlink / ingest | Satellite → ground → pipeline |
| End-to-end (delivery time) | Acquisition → first delivery |
| Hours vs Deadline | Delivered − deadline; <0 early |
| Row Status | Why a row is in or out. Latest attempt = processable image IPR owns (89); + Not captured = all images (95); Earlier attempt (history); Removed - stale duplicate. Replaces Image Row and In Pipeline KPI |
| ISOFIT | Atmospheric-correction step |
| L1C / L2A | Calibrated image / surface reflectance (delivered) |
| Off-nadir | Tilt from straight down |
| P0–P4 | Priority by SLA: 8 / 12 / 16 / 24 / 48h |
| Processable | Captured and ≤ 70% cloud |
| QC / QA | Per-image review / process quality |
| Relative light | Light at acquisition (Very Low–High) |
| Reprocess | Same capture run again; no reason recorded |
| SLA | Hours from acquisition by priority |
| Snapshot | 2026-06-30 16:05 UTC |
| Stale duplicate | Same image + attempt, outdated status |
| Strip | Ground imaged in one pass |
| Stuck | Triggered, no end time |
| Zenith / azimuth | Angle from overhead / compass direction |

### Imaging terms

Frames make a strip; a strip is cut into an image. Also in the workbook's Guide tab.

| Term | Meaning |
| --- | --- |
| Frame | One sensor readout: a thin cross-track slice of ground, all bands. Smallest unit. |
| Strip | All frames from one continuous pass, joined end to end (\~40 km wide). |
| Image | One Image ID = one satellite, one AOI, one date; usually one strip cut to the AOI. |
| Flow | Acquisition (frames stored on board) → Downlink (frames sent to ground) → Ingest (frames assembled into a strip, L0) → Trigger → Processing. |
| Image Complete | All frames of the strip arrived, decided at Downlink/Ingest. Not coverage (see Plan Coverage %). Should not change between attempts; it flips in 7 images. |
| Ingest Wait (h) | Covers Downlink + Ingest. No separate timestamps for those steps. |
| Completeness gate | Proposed check at Ingest, before Trigger. Complete → process; AOI frames present → process, flagged; AOI frames missing → hold, re-downlink or re-task, never rerun. Today 20 of 23 incomplete attempts were processed; 7 of 14 incomplete images failed QC vs 3 of 75 complete. |
| Offset North / East (km) | Target offset from plan (Column\_Map; raw Plan Offset North/East). How far the acquisition target sits from its planned position. Not ground displacement from nadir: view tilt is Off Nadir (°) and Satellite Zenith (°). |

### Teams

Only the teams the brief names. No separate ops team is assumed.

| Team | Role |
| --- | --- |
| IPR | Runs the image pipeline end to end: acquisition → processing → QC → reprocess → delivery. Led by the IPR lead. |
| QA/QC | Per-image review: sets QC Result and QC Finding. |
| Engineering | Owns the pipeline code and systems (stuck runs, ISOFIT, water mask). |
| Customer Success (CS) | Talks to the customer. Sets Customer Status (shown) by hand today. |

Notes have no author field, so their owner is unknown. By wording they come from IPR, QA/QC, CS and ground.
