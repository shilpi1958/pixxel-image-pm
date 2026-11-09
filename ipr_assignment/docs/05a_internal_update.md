# IPR Internal Update

Nov 7, 2026 · @Sj

## To Engineering, IPR and QA/QC

**Subject:** IPR pipeline: 28 images late, plan for the next 2 weeks

Hi all,

Where we are, as of the 30 Jun export:

- **58% of processable images were delivered on time** (52 of 89). **No P0 image met its 8h SLA** (0 of 8).
- **28 images are late,** 19 of them by more than two weeks. 15 belong to our three Tier 1 customers (MineralsCo, AgriSense, UrbanAtlas).
- **What's blocking them:** 5 passed QC but were never released, 10 are waiting for a QC decision, 10 failed QC (8 with bright banding, BBR), and 3 are stuck in processing.
- **Two process gaps:** 74% of attempts were released before QC started, and there is no QC End time, so we can't tell how long review takes.

What we're doing, in order:

1. **Today:** release the 5 QC-passed images, both P0s first (Engineer B).
2. **Days 1–3:** QC decides the 10 pending images in deadline order (QA/QC). Engineer A clears the 3 stuck runs and reprocesses the 2 processing-error failures.
3. **BBR:** the 8 images are on hold, not retried. None of the 8 recovered on an earlier retry. Engineer A and QA scope a fix in week 2.
4. **Week 2:** a P0/P1 lane, QC End and release-time logging, an escalation log, a gate so nothing is released before a QC pass, and a nightly check of 20 contradiction rules that alerts the owner of each break.

What we need from you:

- **Engineering:** confirm the P0/P1 lane can go into the processing queue in week 2.
- **QA/QC:** confirm whether QC is meant to gate release, or whether some reviews happen after release by design.
- **Everyone:** log an escalation (who, when, ticket) when you hand off a blocked image. Today 20 of the 28 late images have no record.

The daily 15-minute stand-up runs from the dashboard's Act now list. Next update: day 5, with the late-image count and the go or no-go for the release gate.

The full plan is in the IPR 2-Week Plan doc.
