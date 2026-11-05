# Notebook — watch the QA calculations happen

- [`qa_pipeline_walkthrough.ipynb`](qa_pipeline_walkthrough.ipynb) is the learning companion to this repo
- Re-derives, step by step, how the QA rule engine turns real files in `data/` into a decision
- Every intermediate number printed, every mask visualized
- Includes an interactive slider: drag the QA-3 cloud threshold, watch the Saskatchewan scene's verdict flip
- Falls back to a printed threshold sweep when run non-interactively (live widget needs a connected frontend)
- Executed end-to-end before committing, so opening it already shows all outputs
- Re-run cells to explore

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r agent/requirements.txt jupyterlab matplotlib ipywidgets
.venv/bin/jupyter lab          # then open notebooks/qa_pipeline_walkthrough.ipynb
```

- Launching Jupyter from the venv picks up the right Python automatically
- The notebook locates the repo root whether started from the root or from `notebooks/`

## What's inside (37 cells)

- **Setup** — imports, path detection, scene discovery
- **Inspect one scene** — the files QA actually reads
- **The data mask** — 4 layers, raw values, NoData; rendered as a 3D point cloud
- **The valid footprint** — why every percentage excludes the empty border
- **The four metrics, re-derived** — `band_count`, `cloud_or_haze_pct` (union!), `quality_mask_coverage_pct`, `interpolated_pct` (band-pixels!)
- **Band-13/15/16 interpolated-pixel localization** — which bands, where, and that they form thin stripes rather than scattered noise; a top-down stripe map, a per-band bar chart, and a true-scale proportion bar
- **All metrics, all 3 scenes** — the same metrics the rule engine works from
- **`rules.json`** — the PRD as data
- **Run the real rule engine** — verify decisions match `agent/decisions.json`
- **Band-aware QA-4 and partial delivery** — the copper-mine scene's per-band and partial-delivery fields, computed live
- **Interactive experiment** — drag the QA-3 threshold, watch the decision flip
- **Challenges** — things to try on your own

## Why this notebook exists

- Turns the repo's finished artifacts back into a teaching tool where every calculation happens visibly
- Rules can be broken deliberately to understand them
