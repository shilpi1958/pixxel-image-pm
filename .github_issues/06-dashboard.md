---
title: "6. Build the monitoring dashboard mockup"
labels: dashboard
---

## Why
Give the PRD and agent output a face — what would pipeline monitoring actually look like day to day.

## Tasks
- [ ] Design a clickable dashboard (image queue, per-image QA status, failure category, retry count, version)
- [ ] Populate with the 3 real images and their real agent decisions from step 5 — no placeholder/fake data
- [ ] Include a detail view per image showing the reasoning trace from the agent

## Acceptance criteria
- Dashboard runs locally and is clickable (not a static image)
- All data shown traces back to real files in `data/` and `agent/decisions.json`
