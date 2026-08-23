# Pixxel Image Product Manager — QA/QC Pipeline Practice Project

A hands-on project that builds the **pipeline monitoring layer for hyperspectral satellite imagery** — the exact problem an Image Product Manager owns at [Pixxel](https://pixxel.space): QA/QC rules, failure categorization, retry/escalation, versioning, and delivery tracking. Built end-to-end against **real commercial hyperspectral imagery**, not synthetic data.

## The one-line pitch

An agent that looks at a hyperspectral scene, reads its quality mask, applies mechanical QA rules, and decides **pass / retry / escalate** — with a logged reasoning trace — plus a monitoring dashboard that shows those decisions against the real images.

## Why this project (the two gaps it closes)

1. **Hands-on hyperspectral data fluency** — what a 23/31-band scene actually looks like, what "quality" means, and what goes wrong between capture and delivery.
2. **Vocabulary translation** — mapping general pipeline-monitoring experience (QA rules, retries, versioning, delivery SLAs) onto domain terms: L1B/L2A processing levels, cloud/quality masks, spectral bands, STAC catalogs.

## What's in the repo

| Folder | Contents |
|---|---|
| [`prd/`](prd/qa-qc-prd.md) | The QA/QC product requirements — pass/fail rules (QA-1…QA-7), failure categories, retry vs. escalate logic, versioning, "delivery ready" definition |
| [`data/`](data/README.md) | 3 **real** Wyvern hyperspectral scenes via their public STAC catalog: a clean crop field (Australia), a **wildfire-smoke scene** (Saskatchewan, May 2025), and an open-pit copper mine (Chile) — each with STAC metadata, quality masks, and previews |
| [`agent/`](agent/SETUP.md) | The **QA triage agent**: executes the PRD's rules as structured conditions against each scene's real metadata + masks, decides pass/retry/escalate, and logs the full reasoning trace → [`agent/decisions.json`](agent/decisions.json) |
| [`dashboard/`](dashboard/README.md) | Clickable pipeline-monitoring dashboard — image queue, per-scene QA status, failure category, retry count, version, reasoning trace. Populated only with the real data above |
| [`docs/`](docs/pipeline-walkthrough.md) | Pipeline walkthrough: raw input, quality mask, and processed output side by side for each scene, tied to specific PRD rules |
| [`notebooks/`](notebooks/README.md) | **The learning notebook** — every QA calculation re-derived step by step on the real data, with an interactive threshold experiment |

## Quick start

```bash
# 1. setup
python3 -m venv .venv && .venv/bin/pip install -r agent/requirements.txt

# 2. run the QA triage agent on the 3 real scenes
.venv/bin/python agent/triage_agent.py --data data
#   → writes agent/decisions.json + agent/logs/*.log

# 3. learn interactively (optional but recommended)
.venv/bin/pip install jupyterlab matplotlib ipywidgets
.venv/bin/jupyter lab            # open notebooks/qa_pipeline_walkthrough.ipynb

# 4. serve the dashboard
python3 -m http.server 8000        # open http://localhost:8000/dashboard/
#   (or open dashboard/index.html directly — data is embedded, no server needed)
```

## What the agent decided (real output, 2026-08-23)

| Scene | Decision | Why (rule fired) |
|---|---|---|
| Clean crop field, Australia | **pass** ✅ | No rule fired — CLEAN, delivery ready |
| Wildfire smoke, Saskatchewan | **retry** 🔁 | QA-3: cloud + smoke obstruct **62.3%** of valid pixels (> 40% threshold) |
| Copper mine, Chile | **pass** ✅ | No rule fired — CLEAN, delivery ready |

Every decision traces to a specific rule in the PRD; the reasoning logs say exactly which metrics were measured and which rules could not be assessed (and why). No "the agent just decided".

## What's genuinely real vs. scoped down

- **Real:** the imagery, the masks, the catalog metadata, the agent's decisions, the numbers on the dashboard.
- **Scoped:** the full-resolution band stacks are 2.2–3.1 GB per scene (the ODP host doesn't support partial downloads), so they're linked by URL in the STAC metadata rather than mirrored. Reflectance-level rules (QA-6/7) and geolocation metrics (QA-5) are implemented and unit-tested but logged as *not assessable* on these scenes — the trace states exactly what could and couldn't be verified.
- **Placeholders:** the PRD's thresholds (40% cloud, 2% dead pixels, …) are starting points, explicitly meant to be tuned against real data — which is what this project does.

## Built with

[DeepSeek Harness](https://github.com/deepseek-ai/DeepSeek-Harness) (the agent framework this project runs in — see [`docs/deepseek-harness-notes.md`](docs/deepseek-harness-notes.md)), Python (numpy/tifffile/rasterio), and vanilla HTML/JS for the dashboard. Imagery from [Wyvern's Open Data Program](https://wyvern.space/open-data/) (CC BY 4.0, attribution: Wyvern Inc.).

## Outreach

This repo is the artifact for a Pixxel **Image Product Manager** application. Suggested framing for the note that points here:

> Hi [name] — I built a practice version of the pipeline-monitoring layer Pixxel's Image PM owns: a QA/QC agent that runs mechanical pass/fail rules against real Wyvern hyperspectral scenes (including a wildfire-smoke scene), decides pass/retry/escalate, and logs its reasoning, with a monitoring dashboard on top. It's all driven by real imagery from Wyvern's open data program. Two things it demonstrates: hands-on fluency with hyperspectral data and QA masks, and translating general pipeline-monitoring practice (QA rules, retries, versioning, delivery SLAs) into this domain's terms. Happy to walk through it.

## Status

✅ PRD · ✅ real data · ✅ pipeline walkthrough · ✅ agent + decisions · ✅ dashboard · ✅ README.
