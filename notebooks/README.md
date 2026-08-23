# Notebook — watch the QA calculations happen

[`qa_pipeline_walkthrough.ipynb`](qa_pipeline_walkthrough.ipynb) is the
learning companion to this repo. It re-derives, step by step, how the QA
agent turns the real files in `data/` into a pass / retry / escalate
decision — with every intermediate number printed, the masks visualized, and
an interactive slider at the end that changes the QA-3 cloud threshold so you
can watch the Saskatchewan scene's verdict flip.

The notebook was **executed end-to-end** before committing, so opening it
already shows all outputs; re-run cells to explore.

## Run it

```bash
# from the repo root
python3 -m venv .venv
.venv/bin/pip install -r agent/requirements.txt jupyterlab matplotlib ipywidgets
.venv/bin/jupyter lab          # then open notebooks/qa_pipeline_walkthrough.ipynb
```

(Launching Jupyter from the venv picks up the right Python automatically; the
notebook locates the repo root whether Jupyter was started from the root or
from `notebooks/`.)

## What's inside (27 cells)

1. **Setup** — imports, path detection, scene discovery
2. **Inspect one scene** — the files QA actually reads
3. **The data mask** — 4 bands, raw values, NoData
4. **The valid footprint** — why every percentage excludes the empty border
5. **The four metrics, each re-derived** — `band_count`, `cloud_or_haze_pct`
   (union!), `quality_mask_coverage_pct`, `interpolated_pct` (band-pixels!)
6. **All metrics for all 3 scenes** — the exact table the agent works from
7. **`rules.json`** — the PRD as data
8. **Run the real agent engine** — and verify the decisions match
   `agent/decisions.json` ✓
9. **Interactive experiment** — drag the QA-3 threshold, watch the decision
10. **Challenges** — things to try on your own

## Why this notebook exists

The repo was built by an agent; the notebook is the part built for *you*: it
turns the finished artifacts back into a teaching tool where you see every
calculation happen and can break the rules to understand them.
