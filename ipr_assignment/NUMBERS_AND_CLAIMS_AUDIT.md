# IPR numbers and claims audit

Audit date: 10 Nov 2026  
Scope: every unique numerical claim in the rendered submission and dashboard. Repeated uses of the same measure are consolidated below. The source of truth is `IPR_Cleaned_Data.xlsx`, with the original `Raw_Data` checked for population counts.

## Outcome

Corrections identified below were applied to the submission on 10 Nov 2026: unsupported escalation and blocked-image counts were removed, ISOFIT was restored to 3 images / 3 attempts, the timing denominator was stated as timestamped attempts, and the undocumented correlation threshold was removed.

## Status key

| Status | Meaning |
| --- | --- |
| Verified | Recalculated from the cleaned workbook and matches the published value within displayed rounding. |
| Wording fix | Number is correct, but its population or unit needs to be stated more precisely. |
| Incorrect | Recalculation disagrees with the published claim. |
| Unsupported | The export has no field or defined derivation that can support the claim. |
| Proposal | A target, effort estimate, or future control rather than an observed result. |

## Population and delivery health

| Published claim | Result | Evidence / required treatment |
| --- | --- | --- |
| 136 export rows | Verified | Raw_Data contains 136 rows. |
| 6 stale duplicates removed; 130 valid rows | Verified | Cleaned workbook has 6 `Removed - stale duplicate` rows and 130 remaining rows. |
| 95 images | Verified | 89 latest processable rows plus 6 not-captured rows. |
| 89 processable images; 6 not captured | Verified | The cleaned workbook has 89 `Latest attempt` rows and 6 `Not captured` rows. |
| 123 processing attempts | Verified | 123 retained processable rows have a Trigger timestamp. There are 124 latest/history rows, but one has no Trigger and is not a processing attempt. |
| 26 images needed more than one run | Verified | 18 images have two triggered attempts and 8 have three. |
| Average 1.38 attempts per processable image | Verified | 123 ÷ 89 = 1.382. |
| 61 delivered; 69% | Verified | 61 of 89 latest processable images have Delivery Status = Delivered. |
| 52 on time; 58% | Verified | 52 of 89 latest processable images are delivered with Hours vs Deadline ≤ 0. |
| 37 missed SLA; 9 delivered late; 28 still open | Verified | 9 delivered images are late and 28 undelivered processable images are past deadline. 9 + 28 = 37. |
| All 28 undelivered processable images are past deadline | Verified | All 28 non-delivered latest processable rows have positive Hours vs Deadline. |
| 11 failed; 7 in progress; 7 QC-passed/not-uploaded; 3 uploaded without QC pass | Verified | These six delivery buckets reconcile exactly to 89 processable images: 61 + 11 + 7 + 7 + 3. |
| No P0 image met SLA; 0 of 8 | Verified | There are 8 latest P0 images and no on-time delivery. |
| 3 P0 images require immediate attention | Verified | Three latest P0 images are undelivered and past SLA. |
| 45 of 95 customer statuses are wrong | Verified | 45 latest/not-captured rows carry a Customer Status conflict. Do not compare raw shown and derived text directly, because status vocabularies differ. |
| 34 blocked images | Unsupported | No `Blocked` field or reproducible derivation exists in the workbook. The submission must define it explicitly before using the count. |
| 25 of 34 blocked images have no recorded escalation | Unsupported | No structured escalation timestamp, target, owner, or ticket field exists. Remove the number. State only that the export cannot show whether escalation occurred. |

## Timing and workflow integrity

| Published claim | Result | Evidence / required treatment |
| --- | --- | --- |
| Ingest average 9.1h; 51% miss target | Verified | 123 timestamped ingest waits average 9.08h. 63 of 123 exceed the 20%-of-SLA target. |
| Processing average 5.2h; 31% miss target | Wording fix | 119 measured processing durations average 5.25h. 37 of 119 exceed the target (31%). If missing timestamps count as misses, the rate is 40 of 123 (33%), not 31%. |
| QC wait average 3.5h; 59% miss target | Wording fix | 113 measured QC waits average 3.50h. 67 of 113 exceed the target (59%). If missing timestamps count as misses, the rate is 77 of 123 (63%), not 59%. |
| No P0/P1/P2 attempt met all three measurable timing targets | Verified | P0: 0/11; P1: 0/17; P2: 0/23. P3: 2/15; P4: 23/57. |
| P0 median delivery is 10.4h against an 8h SLA | Verified | Median End-to-end time for delivered P0 images is 10.4h. |
| 55 of 74 uploads occur before QC Start; 74% | Verified, wording fix | 55 of 74 rows with both timestamps have upload before QC Start. Always say “74% of timestamped attempts.” |
| QC review and upload duration cannot be measured | Verified | QC End is absent, so neither interval has a valid start/end pair. |
| Proposed QC-review target is 8.0h | Proposal | This is a planning target, not a source-derived operational fact. Keep the label “proposed.” |
| End-to-end average is 13.1h; 15% are late | Verified | Delivered images average 13.11h end-to-end; 9 of 61 delivered images are late (14.8%). The row is image-level, not attempt-level. |

## Image completeness, QC, and failure claims

| Published claim | Result | Evidence / required treatment |
| --- | --- | --- |
| 20 incomplete attempts overall; 19 were triggered | Verified | 20 retained processing-history rows are Incomplete; 19 have a Trigger timestamp. |
| 7 of 14 latest incomplete images failed QC versus 3 of 75 complete images | Verified | Latest-image comparison recalculates exactly. |
| BBR: 8 images, 13 attempts, 0 delivered in latest status | Verified | Eight image IDs have BBR on 13 attempts; all eight latest rows are Failed. |
| ISOFIT: 2 images, 1 delivered | Incorrect | Source shows 3 image IDs / 3 ISOFIT attempts. One is now Delivered; two latest rows are Failed. Restore `3 images / 3 attempts; 1 of 3 delivered`. |
| Water Mask: 3 images, 3 attempts, 2 delivered | Verified | Three image IDs / three attempts; latest state is two Delivered and one Failed. |
| Missing metadata: 2 images, 2 attempts, 1 delivered | Verified | Two image IDs / two attempts; latest state is one Delivered and one Failed. |
| 24 delivered images passed with a caveat | Verified | 24 latest delivered images have a Caveat QC Finding. |
| 42 of 78 clean first-pass QC decisions; 54% | Verified | Of 78 first-attempt QC decisions, 42 are Pass with no finding. |
| 3 of 13 QC recovery deliveries; 23% | Verified | Three of 13 image IDs with a QC Fail or Reprocess-required outcome are now Delivered. Use the name `QC recovery delivery rate`; it does not include processing/input failures without that QC outcome. |

## Pattern and cohort claims

| Published claim | Result | Evidence / required treatment |
| --- | --- | --- |
| FF02: 9/25 on time (36%); FF01: 23/33 (70%); FF03: 20/31 (65%) | Verified | Recalculated from latest processable images. |
| Vegetation: 15/33 on time; 6 of 10 latest QC failures | Verified | 15 of 33 are on time; six latest QC Fail rows use Vegetation. |
| Low light: 7/17 on time, 4 QC failures, 8 reprocessed | Verified | All three figures recalculate from latest image context plus attempt history. |
| Very Low light: 2/6 on time | Verified | Recalculated from latest processable images. |
| Clear 32/55 on time; Partial 19/33 on time | Verified | Recalculated from latest processable images. |
| Partial images reprocessed 39% versus Clear 22% | Verified | 13/33 Partial versus 12/55 Clear image IDs have multiple attempts. |
| Jun 1–7 / 8–14 / 15–21 / 22–28 cohort table | Verified | All published weekly image, on-time, QC fail/BBR, incomplete, pass-not-uploaded, coverage, and partial-status counts recalculate exactly. |
| Delivered images include cloud cover up to 68% | Verified | Maximum Cloud Cover % among delivered latest images is 68%. |
| The only image above 70% cloud was not captured | Verified | One retained row is Cloudy and is Not captured. Do not also claim that no image exceeds 70%. |
| Weather and geometry do not explain processing time; correlations ≤ 0.11 | Needs method note | This may be correct, but the correlation calculation and eligible population are not stored in the workbook. Retain only if the calculation is documented in the audit log or remove the numerical threshold. |

## Attention list and customer communication

| Published claim | Result | Evidence / required treatment |
| --- | --- | --- |
| Seven late P0/P1 images | Verified | There are three P0 and four P1 latest undelivered rows past SLA. |
| The seven image IDs, customers, priorities, states, and overdue hours | Verified | All seven rows match the latest processable records. BENGA (167.2h) correctly precedes ODISH (130.3h). |
| UrbanAtlas has two late P0 Dubai images | Verified | Both listed Dubai image IDs are latest P0 records and past SLA. |
| UrbanAtlas also has a separate not-captured image incorrectly shown Delivered | Verified | FF03_20260624_1086_DUBAI is Not captured with Customer Status shown = Delivered. Handle separately from the two-image delay update. |

## Plan, ownership, and future targets

| Published claim | Result | Evidence / required treatment |
| --- | --- | --- |
| 60 hours each for two engineers and QA/QC | Proposal | Capacity assumption. Keep as a planning assumption. |
| Week-2 residual backlog: 8 BBR, 1 incomplete, up to 3 failed retries | Proposal / unsupported | A forward projection, not a current source count. Label as expected residual backlog and state its assumptions. |
| Review 2 ISOFIT incidents; one remains open | Incorrect | Source supports 3 ISOFIT incidents, with two current Failed images. Change the plan and internal update accordingly. |
| Remaining Water Mask and Missing Metadata: 2 images, one each | Verified | One latest Failed image maps to Water Mask history and one to Missing Metadata history. |
| Customer status is derived automatically in Week 2 | Proposal | Correct product action; no source claim to validate. |
| Day 6 review and Day 9 upload gate | Proposal | Sequencing is internally coherent once the Week-1 target reads “Ready for Day 6 review.” |

## Required corrections before the submission is trusted

1. Remove every `25 of 34` escalation statement. Replace with: `The export has no structured escalation record, so it cannot show whether blocked images were escalated or to whom.`
2. Either define `Blocked` in reproducible workbook terms or remove the `34 blocked images` headline and all uses of the count.
3. Restore ISOFIT to `3 images / 3 attempts; 1 delivered and 2 failed` in the note, appendix, plan, and internal update.
4. Restore incomplete-attempt wording to `20 attempts overall, 19 triggered`. Do not use 23.
5. Make timing wording consistent: either use measured-attempt denominators (31% processing, 59% QC wait) or count missing values as misses and use 33% and 63%.
6. Keep the dashboard and 2-page note on the same five metrics and exact definitions. The current shared definition for metric 5 is a QC-outcome recovery rate, not a general processing-failure recovery rate.
7. Keep Aurora explicitly labelled as an assumption/exception. Do not let it silently override the standard delivered definition or a metric without a documented rule.

