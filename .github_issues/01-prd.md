---
title: "1. Write the QA/QC PRD"
labels: prd
---

## Why
Everything downstream (data selection, agent rules, dashboard fields) depends on this. Get it right first.

## Tasks
- [ ] Define QA pass/fail rules for hyperspectral image products (per-band and whole-scene)
- [ ] Define failure categories (e.g. cloud cover, sensor artifact, geometric misalignment, radiometric anomaly, missing bands)
- [ ] Define retry vs. escalate logic — when does the pipeline auto-retry vs. page a human?
- [ ] Define versioning rules — what triggers a new product version vs. a reprocess of the same version
- [ ] Define "delivery ready" — the exact bar a product must clear before it ships to a customer

## Acceptance criteria
- `prd/qa-qc-prd.md` exists and is internally consistent (no rule references a category or field not defined elsewhere in the doc)
- Every rule is stated in terms an agent could execute mechanically (no vague language like "looks bad")
- Doc explicitly separates QA/QC (pipeline monitoring's job) from the image-processing algorithms themselves (not this role's job)
