# IPR Pipeline Health – 2-Page Note

Nov 5, 2026 · @Sj

## Summary

Images are late far more often than they fail, and P0 is worst: no P0 image met its SLA.

| Headline | Value |
| --- | --- |
| On time (processable images) | 58% (52 of 89) |
| Delivered at all | 69% (61 of 89) |
| P0 on time | 0 of 8; 3 never arrived |
| Customer status wrong | 45 of 95 images |

Four causes:

- **No priority lane:** processing and QC wait take the same time at every priority, so P0s queue behind P4s.
- **QC may not gate release:** most uploads are logged before QC starts. Not yet confirmed: it could be late logging rather than a skipped check.
- **Incomplete imagery enters processing:** incomplete images fail QC far more often than complete ones (an association, not proven cause).
- **The data can't measure QC:** there is no QC-end timestamp.

**Next:** the fix for each cause is sequenced in the [IPR 2-Week Plan](https://claude.ai/artifact/7TYRU23LDK93ek3b6BkZGc).

## Pipeline health

Every processable image that wasn't delivered is past its deadline. \
10 of them need no rework, only an upload or a QC decision.

| Bucket | Images | Rule |
| --- | --- | --- |
| Not captured | 6 | Never imaged; out of KPIs |
| Cloudy, not processable | 0 | Over 70% cloud |
| Delivered | 61 | QC pass + upload |
| QC passed, not uploaded | 7 | 5 ready to release; 2 have a stuck run to check first |
| Uploaded without QC pass | 3 | On DataHub, not counted; 2 shown to customers as Delivered while QC is pending |
| In progress | 7 | Processing or in QC |
| Failed | 11 | Processing or QC failed |

- **Cloud isn't the problem:** images up to 68% cloud were delivered.
- **Long-late images:** median 17.9 days old; each needs a ship, re-task or close decision.

## Where time is lost

Averages look fine only because 48h orders dominate. By tier, processing alone breaks the 8h, 12h and 16h targets.

_[Chart: processing time by priority, over all 123 valid attempts. Interactive in the live doc.]_

Four steps, timestamp to timestamp. **Targets are my proposed split of each SLA, not agreed operational targets.**

| Step | Proposed target (% of SLA) | Avg actual (h) | Avg proposed target (h) | Attempts over target |
| --- | --- | --- | --- | --- |
| 1. Acquisition → processing start | 20% | 9.1 | 6.1 | 51% |
| 2. Processing | 30% | 5.2 | 9.2 | 31% |
| 3. Waiting for QC | 10% | 3.5 | 3.1 | 59% |
| 4. QC review (QC start → release) | 25% | −1.4 | 8.0 | Negative in 74% of attempts |
| 5. Release | 15% |  |  |  |
| End-to-end delivery time (per delivered image) | 85% | 13.1 | 26.3 | 21% |

Few attempts meet the three measurable targets (ingest, processing, QC wait), and P0 almost never does. These cover three of the five stages, not the full SLA.

| Measure | Value |
| --- | --- |
| Attempts meeting all three targets | 20% (25 of 123) |
| …at P0, P1 or P2 | 0 |
| P0 meeting the ingest target | 9% |
| P0 meeting the QC-wait target | 18% |

A missing timestamp counts as not met. P4 looks fine only because its 48h window is generous.

**So:** the pipeline treats a P0 like a P4: QC wait is about 3.5h at every priority, first come, first served. And the timestamps can't say how long QC takes: step 4 is negative in 74% of attempts, meaning the upload was logged before QC started.

## Root causes

1. **Priority isn't in the workflow.** Processing and QC run first come, first served; nothing moves a P0 ahead. P0 median delivery is 10.4h against an 8h SLA.
2. **QC sequencing is unclear.** Upload precedes QC start in 74% of attempts, and some images sit on DataHub without a pass. Either QC start is logged late or QA audits after release; IPR / QA must confirm which.
3. **Incomplete imagery is processed anyway.** Almost every incomplete attempt ran, and incomplete images fail QC far more often (table below). No gate holds them for re-downlink or re-task.
4. **BBR recurs.** It is the top failure reason, concentrated in Vegetation, and comes back on retry, so reprocessing alone doesn't fix it (patterns table).

| Incomplete vs complete | Incomplete | Complete |
| --- | --- | --- |
| Attempts processed | 20 of 23 | all |
| Images failing QC | 7 of 14 (50%) | 3 of 75 (4%) |

### Patterns behind them

FF02 and the Vegetation bandset stand out. Cloud and off-nadir angle don't.

| Dimension | Data (89 processable images) | Read |
| --- | --- | --- |
| Satellite | FF02 36% on time vs 65–70%; carries 4 of 8 P0s. FF03 ingest is fastest (6.7h vs \~10h) | Check FF02 downlink slots; partly priority mix |
| Bandset | Vegetation 45% on time; 7 of 11 failures (5 BBR) | Start the BBR investigation here |
| Relative light | Low 41%, Very Low 33% on time; Low has 5 failures and 47% reprocessed | Watch; small sample |
| Cloud | Clear and Partial both 58% on time; Partial reprocessed more (39% vs 22%) | Not driving misses |
| Off-nadir angle | 52–64% on time in every band; BBR at every angle | No pattern |
| Failure reason | 13 BBR, 6 processing errors (3 ISOFIT, 3 water mask), 2 missing-metadata input errors; 40 caveats (19 low SNR, 16 minor haze, 5 artifact reduced) | BBR is the defect to fix; it repeats on retry (3 images had it on every attempt) |

Processing time barely varies with any of these (4.5–5.7h; correlation with angles, cloud and coverage ≤ 0.11). They cost time through failures and reprocessing, not slower runs.

## Immediate actions: 5 cases, 6 images

Ranked by priority, hours late and ease of fix. Two need only a release.

| # | Image | Customer | Priority | State | Overdue | Action (owner) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | FF01\_20260601\_1084\_DUBAI | UrbanAtlas | P0 | Passed QC, never uploaded | 697h | Release today (Eng). Customer has asked for an update |
| 2 | FF01\_20260614\_1040\_GUJAR | MineralsCo | P0 | Passed QC, never uploaded | 375h | Upload today (Eng) |
| 3 | FF02\_20260605\_1088\_DUBAI | UrbanAtlas | P0 | QC pending | 592h | QC decision first in the queue (QA/QC). Second late P0 for UrbanAtlas, so one CS update covers both |
| 4 | FF02\_20260613\_1042\_RAJAS | AgriSense | P1 | Passed QC, but processing never recorded an end | 401h | Confirm the output exists, then release (Eng) |
| 5 | FF01\_20260623\_1026\_NILED, FF03\_20260624\_1086\_DUBAI | AgriSense, UrbanAtlas | P1 | Never captured, but customers are told "Delivered" | n/a | Correct the customer status and offer a re-task (CS) |

After these, 3 more QC-passed images can be released today, and one more (P3, FF01\_20260611\_1089\_GUJAR) has a stuck run to check first. The 3 uploaded without a QC pass need a QC decision; 2 of them show Delivered to customers.

## Measure it: top 5 daily metrics

Headline: on-time delivery, 58% (P0 0%). Values cover the June export.

| # | Metric | Numerator | Denominator | Current |
| --- | --- | --- | --- | --- |
| 1 | On-time delivery % | Processable images delivered (QC pass + upload) by their deadline | Processable images whose deadline has passed | 58% (52/89); P0 0/8 |
| 2 | Late images | Processable images not delivered and past their deadline | A count, split by state | 28: 7 QC passed but not uploaded, 3 uploaded without QC, 7 in progress, 11 failed |
| 3 | Delivery time: median / slowest 10%, by priority | Hours from acquisition to first delivery | Delivered images in that priority | 10.9h / 17.8h; P0 median 10.4h against an 8h SLA |
| 4 | First-pass QC pass % | Images that pass manual QC on attempt 1 | Attempt-1 images with a QC decision (pass, fail, or reprocess required) | 83% (65/78) |
| 5 | Reprocess success % | Reprocessed images that end up delivered | Processable images with 2 or more attempts | 85% (22/26) |

The choice of denominator barely moves the headline:

| Denominator | On time |
| --- | --- |
| All 95 images | 55% |
| 89 processable (used here) | 58% |
| Excluding images ≥ 60% cloud | 61% |

## Data fixes, in four themes

The metrics above are only as good as these fixes. QC can't be timed until the first row lands.

| Theme | Gaps today | Fix |
| --- | --- | --- |
| Observability | No QC-end time; no per-step processing times (L1C / ISOFIT / L2A); no order or export timestamp | Log QC start and end, each processing step and order time; stamp each export |
| Workflow integrity | Upload before QC start (74% of attempts); stale status text (41 of 123); 3 reruns after delivery with no reason | Reject out-of-order timestamps; fixed status lists; require a rerun reason |
| Data integrity | 6 duplicate rows; priority changed on retry (21 images); mixed labels; 8 QC Results left Pending after a verdict | Unique key Image ID + attempt; lock priority after attempt 1; record result and reason together |
| Customer visibility | Customer status wrong for 45 of 95; no escalation log (25 of 34 blocked images show none) | Derive status from pipeline state; log Escalated At, Escalated To and ticket ID |

All 15 gaps, the cleaning decisions and the checks to enforce at the source: Appendix.

## Assumptions and open questions

**How the numbers are counted**

- One row per image and attempt; the latest valid attempt is the image's row.
- Priority and SLA locked to attempt 1 (21 images changed priority on a retry).
- Delivered = QC pass + upload. A pass with a caveat counts, shown apart.
- The 6 never-captured images are left out of processable-image KPIs.
- The SLA is assumed to start at acquisition; the export has no order time.

**For IPR / QA**

- **Why are 74% of attempts uploaded before QC starts?** DataHub as QC staging is ruled out (no QC fail was ever uploaded). Either QC start is logged late, or a QA audit runs after release.
- **Does the SLA start at acquisition or at order?** If it's order time, every on-time number here is optimistic.
- **Is moderate BBR a fail?** I mapped Severe and Moderate BBR to Fail. If moderate banding is sometimes acceptable, that row becomes Pass with a caveat.
- **How long does a manual QC review take, and where is QC recorded?** A rough estimate per bandset helps; whether that system can take QC End decides if week 2's logging is a setting or a build.
- **Do the proposed step targets fit?** Ingest 20, processing 30, QC wait 10, QC review 25 and release 15% of SLA.
- **Why are images reprocessed?** 23 of 34 reprocesses followed a QC pass, and 3 delivered images were reworked. No reason is recorded.

## Index: the brief's questions

|  | Question | Short answer | Where |
| --- | --- | --- | --- |
| A | Processing health | 95 images: 89 processable, 6 not captured. Of the 89: 61 delivered, 7 in progress, 11 failed, 7 passed QC but not uploaded, 3 uploaded without a QC pass | Pipeline health |
| B | Images needing attention | 5 cases, 6 images: two P0s that only need a release, a P0 waiting for QC, a stuck P1 that passed QC, and two never-captured images shown as Delivered | Immediate actions |
| C | Patterns | FF02 (36% on time) and Vegetation (7 of 11 failures, 5 BBR) stand out; incomplete images fail far more; cloud and off-nadir angle show no pattern | Root causes |
| D | Duplicates and attempts | One row per Image ID + attempt (6 stale duplicates removed); the latest valid attempt is the image's row; SLA locked to attempt 1 | Assumptions; Appendix |
| E | What counts as delivered | QC Result Pass and uploaded; a pass with a caveat counts, shown apart. SLA assumed to run from acquisition | Assumptions; Top 5, metric 1 |
| F | Data gaps to fix first | No QC-end time, upload before QC (74%), wrong customer status (45 of 95), no escalation log; 15 in all | Data fixes; Appendix |
