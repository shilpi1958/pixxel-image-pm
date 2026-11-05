# Pixxel Image Product Manager — QA/QC Pipeline Practice Project

**🔗 Live dashboard: [shilpi1958.github.io/pixxel-image-pm/dashboard/](https://shilpi1958.github.io/pixxel-image-pm/dashboard/)**

- A hands-on project practicing the pipeline monitoring layer for hyperspectral satellite imagery
- The kind of problem an Image Product Manager role at [Pixxel](https://pixxel.space) would involve
- Built against real commercial hyperspectral imagery, not synthetic data
- A deterministic rule engine (no LLM, no ML) reads a scene's quality mask and applies mechanical QA rules
- Decides **pass / retry / escalate** with a logged reasoning trace
- A dashboard shows the decisions against the real images

## Why this project

1. **Hands-on hyperspectral data fluency** — what a 23/31-band scene looks like, and what "quality" means for it
2. **Vocabulary translation** — QA rules, retries, versioning, SLAs → L1B/L2A, cloud/quality masks, spectral bands, STAC catalogs

## The centerpiece: interpolated pixels in a clean scene

- The copper-mine scene (Atacama Desert, Chile) is the deepest evidence in this repo
- Atmospherically perfect — 0% cloud, 0% haze — but 3 wavelength bands each have a thin stripe of pixels that Wyvern's quality mask flags as interpolated (filled in, not measured)
- The full 2.07 GB hyperspectral band stack was pulled for this scene and QA-6/QA-7 run against real reflectance values — the only scene assessed that deeply
- Full writeup: [live dashboard](https://shilpi1958.github.io/pixxel-image-pm/dashboard/) → copper-mine scene detail view

## What's in the repo

| Folder | Contents |
|---|---|
| [`prd/`](prd/qa-qc-prd.md) | QA/QC rules (QA-1…QA-7), failure categories, retry/escalate logic, delivery-ready definition |
| [`data/`](data/README.md) | 3 real Wyvern scenes: clean crop field (Australia), wildfire smoke (Saskatchewan), copper mine (Chile) |
| [`agent/`](agent/SETUP.md) | QA rule engine — executes the PRD's rules against real metadata + masks → [`agent/decisions.json`](agent/decisions.json) |
| [`dashboard/`](dashboard/README.md) | Clickable pipeline-monitoring dashboard — raw input, mask, output, decision, and analysis per scene ([live](https://shilpi1958.github.io/pixxel-image-pm/dashboard/)) |
| [`notebooks/`](notebooks/README.md) | Learning notebook — every QA calculation re-derived on the real data |

## Quick start

```bash
# 1. setup
python3 -m venv .venv && .venv/bin/pip install -r agent/requirements.txt

# 2. run the QA rule engine on the 3 real scenes
.venv/bin/python agent/triage_agent.py --data data
#   → writes agent/decisions.json + agent/logs/*.log

# 3. learn interactively (optional but recommended)
.venv/bin/pip install jupyterlab matplotlib ipywidgets
.venv/bin/jupyter lab            # open notebooks/qa_pipeline_walkthrough.ipynb

# 4. serve the dashboard
python3 -m http.server 8000        # open http://localhost:8000/dashboard/
#   (or open dashboard/index.html directly — data is embedded, no server needed)
```

## What the rule engine decided

| Scene | Decision | Why |
|---|---|---|
| Clean crop field, Australia | pass ✅ | No rule fired — CLEAN, delivery ready |
| Wildfire smoke, Saskatchewan | retry 🔁 | QA-3: cloud + smoke obstruct **62.3%** (> 40% threshold) |
| Copper mine, Chile | pass ✅ | CLEAN, delivery ready — the only scene with QA-6/QA-7 run against real reflectance |

- Every decision traces to a specific rule; logs state exactly which metrics were measured and which rules couldn't be assessed, and why

## What's genuinely real vs. scoped down

- **Real:** imagery, masks, catalog metadata, rule-engine decisions, dashboard numbers
- **Scoped by default:** band stacks aren't mirrored (2.2–3.1 GB each), so QA-6/QA-7 log as *not assessable* unless one is supplied — the copper-mine scene is the one exception
- Full breakdown, including the band-aware/region-aware checks and their real numbers: the [live dashboard](https://shilpi1958.github.io/pixxel-image-pm/dashboard/)

## Built with

- Python (numpy/tifffile/rasterio) for the rule engine and analysis
- Vanilla HTML/JS for the dashboard
- Imagery from [Wyvern's Open Data Program](https://wyvern.space/open-data/) (CC BY 4.0, attribution: Wyvern Inc.)

## Note on framing

This project simulates what a hyperspectral Image PM's pipeline-monitoring work would likely involve, inferred from public information — not based on a real Pixxel job description or a conversation with anyone there.
