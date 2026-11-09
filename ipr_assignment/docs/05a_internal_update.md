# IPR Internal Update

Nov 7, 2026 · @Sj

## To Engineering, IPR and QA/QC

**Subject:** IPR pipeline: 28 images late, plan for the next 2 weeks

Hi all,

**Where we are,** from the tracker export of 30 Jun:

| Measure | Now |
| --- | --: |
| Captured images delivered on time | 58% (52 of 89) |
| P0 images within their 8h SLA | 0 of 8 |
| Late images | 28 |
| Processing runs uploaded before QC started | 74% |

**Why the 28 images are late:**

| Blocker | Images |
| --- | --: |
| Passed QC, never uploaded | 5 |
| Passed QC, but processing never finished | 2 |
| Waiting for a QC decision | 10 |
| Processing failed with an error | 2 |
| On hold for a bright-banding defect (BBR) | 8 |
| Image data arrived incomplete | 1 |
| **Total** | **28** |

## What we're doing in the next two weeks

**Week 1 (Days 1–5): get the late images to customers**

| What we're doing | Owner | Days |
| --- | --- | --- |
| Upload the 5 QC-passed images, both P0s first | Eng B | 1 |
| Give a QC verdict on the 10 waiting images, nearest deadline first, and keep the QC queue sorted by deadline | QA/QC | 1–3 |
| Finish processing on the 2 stalled images, and reprocess the 2 failed ones once | Eng A | 1–3 |
| Build a way to process P0/P1 images ahead of lower priorities | Eng A | 3–5 |

**Week 2 (Days 6–10): stop new images going late**

| What we're doing | Owner | Days |
| --- | --- | --- |
| Start processing P0/P1 images ahead of lower priorities | Eng A | 6–7 |
| Record when QC starts, when it finishes, and when each image is uploaded | Eng B | 6–7 |
| Rate how bad the banding is on the 8 held images and estimate a fix | Eng A, QA/QC | 6–10 |
| Stop any image being uploaded before it passes QC; uploading a P0 early needs QA/QC sign-off | Eng B, QA/QC | 9 |

The rest of the work, with hours, is in the IPR 2-Week Plan.

**Targets:**

| Measure | Now | End of week 1 | End of week 2 |
| --- | --: | --: | --: |
| Late images | 28 | about 14 | 12 or fewer |
| Late P0/P1 images | 7 | 1 | 1 (a BBR hold) |
| Images uploaded without passing QC | 3 | each one recorded | 0 new from Day 9 |

**What we need from you:**

- **Engineering:** confirm owners on Day 1, and confirm we can move P0/P1 images ahead in the processing queue, before the build starts on Day 3.
- **QA/QC:** before Day 9, tell us if any review is meant to happen after upload. If not, from Day 9 nothing is uploaded before it passes QC.
- **Everyone:** when you hand a stuck image to another team, record who, when and the ticket. Most late images have no record today (20 of 28).

The daily 15-minute stand-up works through the dashboard's Act now view: the images that need action today. Next update on Day 5: the late-image count against the week 1 target, and whether blocking unchecked uploads is ready for Day 9.
