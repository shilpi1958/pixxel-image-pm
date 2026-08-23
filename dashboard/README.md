# Dashboard — pipeline monitoring mockup

A clickable, dependency-free single-page monitoring dashboard for the QA
pipeline. Populated entirely with **real data**: the 3 Wyvern scenes in
`data/` and the agent's actual decisions in `agent/decisions.json`. No
placeholder or fake data.

## Run

```bash
# from the repo root — any static server works, e.g.:
python3 -m http.server 8000
# then open http://localhost:8000/dashboard/
```

The page also works if you open `dashboard/index.html` directly from disk
(`file://`) — the scene data is embedded in `dashboard/data.js` precisely so
the dashboard needs no server and no network.

## What you see

- **Queue view** — one card per scene: thumbnail, role, scene ID, platform,
  decision badge (pass / retry / escalate), failure category, retry count,
  version, delivery-ready state.
- **Detail view** — click any card: large preview, scene facts (from the STAC
  metadata), every QA metric (from the real masks), the full per-rule
  evaluation table in PRD order with reasoning, the not-assessed list, and a
  link to the scene's source files in `data/`.

## Regenerating after a re-run of the agent

```bash
.venv/bin/python agent/triage_agent.py --data data   # refresh decisions.json
.venv/bin/python dashboard/build_data.py             # refresh dashboard/data.js
```

`dashboard/data.js` records the `generated_at` timestamp from the agent run,
so a stale dashboard is visible at a glance.
