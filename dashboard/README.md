# Dashboard — pipeline monitoring mockup

- A clickable, dependency-free single-page dashboard
- Populated entirely with real data: the 3 Wyvern scenes in `data/` and the rule engine's actual decisions in `agent/decisions.json`
- No placeholder or fake data

## Run

```bash
python3 -m http.server 8000
# then open http://localhost:8000/dashboard/
```

- Also works opened directly from disk (`file://`) — scene data is embedded in `dashboard/data.js`, so no server or network is needed

## What you see

- **Queue view** — one card per scene: thumbnail, role, scene ID, platform, decision badge
- Also on the card: failure category, retry count, version, delivery-ready state
- **Detail view** — preview, STAC facts, both real masks rendered, every QA metric
- Also in detail view: full per-rule evaluation table with reasoning, not-assessed list
- Also in detail view: delivery-ready state including `delivery_ready_partial`/`excluded_bands` (PRD §6), link to source files
- **Per-scene findings** — the copper-mine scene's detail view includes a written note on its real sensor defect (679/699/711nm)
- Sourced from `dashboard/build_data.py`'s `SCENE_NOTES` — hand-written, kept separate from the rule engine's own decision output
- Mask previews are pre-rendered PNGs from the real TIFFs (`dashboard/make_mask_previews.py`) since browsers can't render GeoTIFFs natively
- Still real data, not synthetic

## Regenerating after a re-run of the rule engine

```bash
.venv/bin/python agent/triage_agent.py --data data   # refresh decisions.json
.venv/bin/python dashboard/build_data.py             # refresh dashboard/data.js
```

- `dashboard/data.js` records the `generated_at` timestamp from the run, so a stale dashboard is visible at a glance
