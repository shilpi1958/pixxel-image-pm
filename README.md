# Pixxel Image Product Manager — Practice Project

A self-directed project to build hands-on fluency in the problem space of an **Image Product Manager** role at [Pixxel](https://pixxel.space) (hyperspectral satellite imaging), and to learn **DeepSeek Harness** — a new open-source AI agent framework — in the process.

## Why this project

Pixxel's Image PM owns the **pipeline monitoring layer**: QA/QC rules, failure categorization, retry/reprocessing logic, versioning, and delivery tracking for hyperspectral imagery. They do not own the image-processing algorithms themselves.

Two real gaps this project is meant to close:

1. **Hands-on understanding of hyperspectral data** — what it actually looks like, what "quality" means for a 23-band sensor, and what can go wrong between capture and delivery.
2. **Vocabulary translation** — mapping general pipeline-monitoring experience (QA rules, retries, versioning, delivery SLAs) onto this domain's specific terms (L1B/L2A processing levels, cloud/quality masks, spectral bands, STAC catalogs).

## Data source

[Wyvern's Open Data Program](https://wyvern.space/open-data/) — free, public, real commercial hyperspectral satellite imagery. 23 spectral bands, STAC-compliant catalog, includes L1B/L2A processing levels and built-in cloud/quality masks. No signup required. CC BY 4.0 licensed.

## What's in this repo

| Folder | Contents |
|---|---|
| `prd/` | The QA/QC product requirements doc — pass/fail rules, failure categories, retry vs. escalate logic, versioning, "delivery ready" definition |
| `data/` | 3 real Wyvern images pulled via their public STAC catalog (clean crop field, wildfire scene with real quality issues, mine/solar site) |
| `agent/` | DeepSeek Harness triage agent — takes the PRD's rules + image metadata/quality mask, decides pass/retry/escalate, logs its reasoning |
| `dashboard/` | Clickable monitoring dashboard mockup populated with the 3 real images and the agent's actual decisions |
| `docs/` | Pipeline walkthrough — raw input, quality mask, and processed output shown side by side for each image |

## Build order

1. **PRD** — define the rules everything else depends on
2. **Pull real data** — 3 Wyvern images via STAC
3. **Pipeline walkthrough doc** — prove real understanding of the data
4. **Set up DeepSeek Harness** — get one basic test tool working
5. **Build the triage agent** — the differentiator: an agent *executing* the QA rules, not just a doc describing them
6. **Build the monitoring dashboard** — real images, real agent decisions, no fake data
7. **Package for outreach** — README ties it together; share with the right person, not a cold CTO email

## Status

See [issues](../../issues) for tracked tasks and acceptance criteria per step.
