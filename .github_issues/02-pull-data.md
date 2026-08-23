---
title: "2. Pull real data from Wyvern's Open Data Program"
labels: data
---

## Why
Real imagery, not synthetic/mocked data, is the whole point — it's what proves hands-on understanding.

## Tasks
- [ ] Browse Wyvern's public STAC catalog
- [ ] Select and download 1 clean scene (e.g. crop field, minimal quality issues)
- [ ] Select and download 1 scene with real quality issues (e.g. wildfire smoke/burn scar)
- [ ] Select and download 1 industrial/infra scene (e.g. mine or solar site)
- [ ] Save each with its STAC metadata, quality/cloud mask, and both L1B and L2A products where available

## Acceptance criteria
- `data/` contains 3 image sets, each with raw bands, quality mask, and STAC metadata JSON
- A short `data/README.md` notes source URL, acquisition date, and why each scene was picked
