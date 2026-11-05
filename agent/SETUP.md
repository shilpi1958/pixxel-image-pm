# Rule engine setup & usage

- The rule engine (deterministic, rules-based — no LLM) executes the PRD's QA rules against real scene artifacts and decides **pass / retry / escalate** with a logged reasoning trace

## 1. Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r agent/requirements.txt
```

- Requires Python 3.10+
- `rasterio` is only needed if you supply a local band stack (COG) to assess QA-6/QA-7 — mask/metadata rules work without it

## 2. Run

```bash
# run on all scenes in data/ (writes agent/decisions.json + agent/logs/*.log)
.venv/bin/python agent/triage_agent.py --data data

# same, but also assess QA-6/QA-7 from a local COG for one scene folder
.venv/bin/python agent/triage_agent.py --data data \
    --cog 01-clean-cropfield-australia=/path/to/scene.tiff
```

| Output | Contents |
|---|---|
| `agent/decisions.json` | Per-scene metrics, per-rule evaluations, decision, retry count, version, delivery-ready |
| `agent/logs/<scene_id>.log` | Human-readable reasoning trace |

## 3. How it works

1. **`agent/rules.json`** — the PRD's rules as structured data; mirrors `prd/qa-qc-prd.md` §2–§6
2. **`agent/analyze_scene.py`** — reduces each scene to metrics
   - Band count, quality-mask coverage, cloud/haze/shadow %
   - Interpolated-pixel fraction, full-band dropout, worst high-value-band fraction
   - With a COG: reflectance out-of-bounds (QA-6), band correlation (QA-7), worst spatial-tile correlation
3. **`agent/qa_rules.py`** — the mechanical engine
   - Rules evaluated in order, first failure decides the outcome
   - `not_assessable` metrics never fail a rule
   - Partial-delivery fields per PRD §5
4. **`agent/triage_agent.py`** — CLI orchestration, decisions.json + logs

- Metrics the public catalog doesn't provide (geolocation RMSE, co-registration offset, AOI coverage, reflectance without a COG) are reported as **not assessable**
- Never silently assumed to pass

## 4. Tests

```bash
.venv/bin/python agent/tests/test_qa_rules.py
```

- 13 tests cover every rule's pass/fail path, decision routing, and QA-6/QA-7 against a synthetic band stack
- The band-aware QA-4 check, tile-aware QA-7 check, and partial delivery are verified against real scene data (see the copper-mine scene in the [dashboard](../dashboard/)) but have no dedicated unit tests

## 5. Notes / honest limitations

- QA-1 stays L1B-gated — on the repo's L2A scenes it's *not applicable*, though its metric (band count) is still recorded
- QA-4 applies to both L1B and L2A — the pixel_quality_mask it reads is delivered on L2A products in this catalog
- The repo doesn't mirror 2–3 GB per-scene COGs by default
- QA-6/QA-7 are not assessable without one — supply `--cog` to exercise them
- **Exception:** `03-copper-mine-chile`'s real stack was pulled and QA-6/QA-7 run against it
- Passing results in `data/03-copper-mine-chile/band_stack_analysis.json`
