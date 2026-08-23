# Agent setup & usage

The triage agent executes the PRD's QA rules against real scene artifacts and
decides **pass / retry / escalate** with a logged reasoning trace.

## 1. Setup

```bash
# from the repo root
python3 -m venv .venv
.venv/bin/pip install -r agent/requirements.txt
```

Requires Python 3.10+. `rasterio` is only needed if you supply a local band
stack (COG) to assess QA-6/QA-7; mask/metadata rules work without it.

## 2. Run

```bash
# run on all scenes in data/ (writes agent/decisions.json + agent/logs/*.log)
.venv/bin/python agent/triage_agent.py --data data

# same, but also assess QA-6/QA-7 from a local COG for one scene folder
.venv/bin/python agent/triage_agent.py --data data \
    --cog 01-clean-cropfield-australia=/path/to/scene.tiff
```

Outputs:

| File | Contents |
|---|---|
| `agent/decisions.json` | structured decisions for the dashboard — per scene: metrics, per-rule evaluations, decision, retry count, version, delivery-ready |
| `agent/logs/<scene_id>.log` | human-readable reasoning trace per scene |

## 3. How it works

1. **`agent/rules.json`** — the PRD's QA rules as structured data (rule order,
   levels, thresholds, categories, retry-vs-escalate routing). This is the
   single source the engine reads; it mirrors `prd/qa-qc-prd.md` §2–§4.
2. **`agent/analyze_scene.py`** — reduces each scene's delivered artifacts to
   metrics: band count (vs the platform's expected count), quality-mask
   coverage of the scene footprint, cloud/haze/cloud-shadow percentages
   (from the 4-band data mask), interpolated-pixel fraction and full-band
   dropout (from the pixel quality mask), and — only if a COG is supplied —
   reflectance out-of-bounds fraction (QA-6) and mean band-to-band correlation
   (QA-7).
3. **`agent/qa_rules.py`** — the mechanical rule engine: rules evaluated in
   order; first failing rule determines the outcome; retry vs escalate per
   PRD §4; `not_assessable` metrics are reported but never fail a rule.
4. **`agent/triage_agent.py`** — CLI orchestration, decisions.json + logs.

Metrics the public catalog does not provide (geolocation RMSE, co-registration
offset, tasked-AOI coverage, and any reflectance-level check without a COG) are
reported as **not assessable** in the trace — the agent never silently assumes
them to pass.

## 4. Tests

```bash
.venv/bin/python agent/tests/test_qa_rules.py
```

13 tests cover every rule's pass/fail path, decision routing (clean pass,
cloud retry, retry-ceiling escalate, mask-gap escalate, L1B band-count and
sensor-artifact escalate), and the QA-6/QA-7 metric computations against a
synthetic band stack.

## 5. Notes / honest limitations

- QA-1 and QA-4 are L1B-gated in the PRD, so on the repo's L2A scenes they are
  evaluated as *not applicable*; their metrics (band count, interpolated
  pixels) are still recorded.
- The repo deliberately does not mirror the 2–3 GB per-scene COGs (see
  `data/README.md`), so QA-6/QA-7 are not assessable on the real scenes in
  this repo. The code paths are implemented and unit-tested; supply a COG with
  `--cog` to exercise them on real data.
