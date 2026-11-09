# IPR 2-Week Plan

Nov 7, 2026 · @Sj

## Goals

- **Recover priority images:** upload the late P0/P1 images first.
- **Recover throughput:** upload as many other late images as possible.
- **Prevent recurrence:** move P0/P1 ahead in processing and QC, and block uploads that haven't passed QC.
- **Make delays visible:** log when QC starts and ends, when each image is uploaded, and every escalation.
- **Clean the tracker:** fix the records that are wrong today, and automate every field that can be automated.

## Targets

| Measure | Now | End of week 1 | End of week 2 |
| --- | --- | --- | --- |
| Late images | 28 | about 14 | 12 or fewer, each with an owner and ETA |
| Late P0/P1 images | 7 | 1 | 1 (a P1 BBR hold) |
| P0/P1 processed ahead of lower priorities | no | built | in use from Day 7; measured once new orders resume |
| Images uploaded without a QC pass | 3 | logged, not blocked | 0 new from Day 9, except signed P0 overrides |
| Attempts uploaded before QC started | 74% |  | 0% from Day 9 |
| New attempts with QC Start, QC End and upload time | 0% |  | 100% from Day 7 |
| Delivered images that passed QC with a caveat (Low SNR, haze, artifact), re-reviewed | 0 of 24 | all 24 |  |
| Images showing customers the wrong status | 45 of 95 | 0 |  |

What stays late at the end of week 2:

| Group | Images | Why it stays late |
| --- | --: | --- |
| BBR holds | 8 | The fix starts in week 3; week 2 only works out what it needs |
| Incomplete image | 1 | Needs ground to resend it or Tasking to capture it again; outside this team |
| QC fails or reprocessing that doesn't recover (estimate) | up to 3 | One retry each; anything still failing moves to week 3 |
| **Total** | **12 or fewer** |  |

## Team

| Who | Owns | Hours |
| --- | --- | --: |
| Engineer A | Processing: stuck runs, retries, P0/P1 priority processing, BBR investigation | 60h |
| Engineer B | Uploads and data: uploads, QC gate, logging, alerts | 60h |
| QA/QC | QC decisions, upload sign-off, caveat recheck, BBR review, QC criteria | 60h |
| IPR Lead | Priorities, escalations, customer updates |  |

**Assumptions:**

- No new images arrive during the two weeks.
- Each person has 6 productive hours a day.
- Engineer owners are confirmed on Day 1.
- **Upload** = the image is sent to DataHub. An image can be uploaded without passing QC.
- **Delivered** = the image passed QC and was uploaded. Only delivered images count as done.
- **Who uploads images:**
  - *What we saw:* 7 images passed QC but were never uploaded. Passing QC does not upload an image on its own, and the data doesn't say who uploads it.
  - *What we assume:* uploading an image after it passes QC is a manual step, and Eng B can do it.
  - *To confirm:* with IPR on Day 1. If someone else does it, Eng B's upload hours move to them.

## Order for clearing the 28 late images

| Order | Images | Next step | Owner |
| --: | --- | --- | --- |
| 1 | 6 of the 7 late P0/P1 (the 7th is a BBR hold, row 6) | Upload 2 QC-passed P0s on Day 1; QC decisions on 3; check 1 stuck run that already passed QC | IPR Lead |
| 2 | 3 QC pending, already shown to customers as Delivered | Confirm, or pull back and tell the customer | QA/QC |
| 3 | 4 QC-passed: 3 ready, 1 with a stuck run | Upload | Eng B |
| 4 | 4 QC pending | QC decision; upload the passes | QA/QC |
| 5 | 2 processing errors | Retry once, after a frames check | Eng A |
| 6 | 9 holds (8 BBR, 1 incomplete) | No retries; tell customers; request re-downlink | IPR Lead |

Across the rows: 5 QC-passed images ready to upload, 2 QC-passed with stuck runs, and 10 waiting for a QC decision. The image-level list is the dashboard's Act now view.

## Week 1: clear what customers feel (days 1–5)

| Problem | Fix | Owner | Hours | Days |
| --- | --- | --- | --- | --- |
| Engineer skills and QC review time are unknown | Confirm owners; time the first QC reviews | IPR Lead |  | 1 |
| 5 images passed QC but were never uploaded (2 are P0) | Upload them, P0s first | Eng B | Eng B 2.5h, QA/QC 1.25h | 1 |
| QC is first come, first served, so P0s wait behind P4s | Sort the QC queue by deadline | QA/QC | QA/QC 1h | 1, then daily |
| 10 images are waiting for a QC decision | Decide them in deadline order | QA/QC | QA/QC 7.5h | 1–3 |
| 3 runs never finished | Recover or re-trigger each one | Eng A | Eng A 6h | 1–2 |
| 2 images failed on processing errors | Retry each once, after checking all frames arrived | Eng A | Eng A 6h, QA/QC 2h | 2–3 |
| 3 images were uploaded without a QC pass | Warn and log any upload without a QC pass | Eng B | Eng B 15h, QA/QC 1.5h | 2–5 |
| P0/P1 wait in the same processing queue as P4 | Build a way to process P0/P1 images ahead of lower priorities; QC and upload checks still apply | Eng A | Eng A 18h | 3–5 |
| 24 delivered images passed with a caveat, not cleanly | Re-review them; flag any that should have failed | QA/QC | QA/QC 12h | 3–5 |
| 45 images show customers the wrong status | Correct them, the 4 wrongly shown as Delivered first | CS |  | 1–3 |
| Customers with late P0/P1 images or BBR holds have no update | Send each one a status and a next-update date | CS |  | as decided |
| 6 images were never captured | Get a retake date, or close with the customer | Tasking |  | by 3 |
| The tracker has 6 duplicate rows | Remove them | Eng B | Eng B 2h | 2 |

## Week 2: stop new misses and measure (days 6–10)

| Problem | Fix | Owner | Hours | Days |
| --- | --- | --- | --- | --- |
| P0/P1 priority processing is built but not in use | Start using it; test it on the week 2 retries first | Eng A | Eng A 6h | 6–7 |
| QC time can't be measured: no QC End or upload time | Log QC Start, QC End and upload time | Eng B | Eng B 12h | 6–7 |
| Stalled runs and late images go unnoticed | Alert the owning team when a run stalls or an image passes its SLA; log the escalation | Eng B | Eng B 18h | 8–10 |
| The week 1 upload check only warns | Block uploads without a QC pass; a P0 override needs QA/QC sign-off | Eng B | Eng B 3h, QA/QC 1.5h | 9 |
| BBR fails on every retry, cause unknown | QA/QC grades severity on all 8 holds; Eng A finds likely causes and estimates a fix | Eng A | Eng A 18h, QA/QC 14h | 6–10 |
| QC verdicts rest on free-text notes | Write pass / caveat / fail criteria per bandset, with SNR and haze limits | QA/QC | QA/QC 6h | 6–8 |
| Images that pass QC in week 2 still need uploading | Upload each the day it passes | Eng B | Eng B 3.5h | ongoing |
| Stretch: contradictions in the tracker are found only by hand | Nightly check that flags them to the owner | Eng B | Eng B 9h | only if Week 1 runs under estimate |

Engineer B is booked 56h of 60 before the stretch item, so it starts only if Week 1 frees time.
