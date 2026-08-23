---
title: "5. Build the QA triage agent"
labels: agent
---

## Why
This is the differentiator: not just designing QA rules on paper, but showing an agent actually execute them against real data with logged reasoning.

## Tasks
- [ ] Feed the agent the PRD's QA rules (as structured input, not free text)
- [ ] Feed the agent each image's metadata + quality mask
- [ ] Agent outputs one of: pass / retry / escalate, per image
- [ ] Agent logs its reasoning trace (which rule fired, why)

## Acceptance criteria
- Running the agent against all 3 images produces 3 decisions + reasoning logs
- Decisions are traceable to specific PRD rules (no "the agent just decided")
- Output saved as structured data (`agent/decisions.json` or similar) for the dashboard to consume
