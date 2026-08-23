# Data — 3 real Wyvern hyperspectral scenes

Real imagery pulled from [Wyvern's Open Data Program](https://wyvern.space/open-data/) via their public
STAC catalog. No synthetic data anywhere in this repo.

- **Catalog root:** <https://wyvern-odp.com/catalog.json> (STAC 1.0.0, browsable at <https://opendata.wyvern.space/>)
- **License:** [CC BY 4.0](https://www.wyvern.space/blog/wyvern-launches-open-data-program-to-provide-unrestricted-hyperspectral-data-access)
  — free to use with attribution to Wyvern. (Note: individual STAC items carry `"license": "proprietary"`,
  but Wyvern's program announcement states the ODP release is CC BY 4.0; the item-level field is stale.)
- **Processing level:** all three scenes are **L2A** surface reflectance (the delivery product in the PRD).
  L1B radiance is not offered for these scenes in the ODP.

## The three scenes

| Folder | Scene ID | Platform | Bands | Date (UTC) | Location | Why picked |
|---|---|---|---|---|---|---|
| `01-clean-cropfield-australia` | `wyvern_dragonette-003_20250319T000402_d5ebab06_l2a` | Dragonette-003 | 31 | 2025-03-19 | Victoria, Australia (144.4°E, 38.2°S) | **Clean scene.** 0% cloud, 0% haze, 100% clear pixels, zero interpolated pixels → expected to pass every QA rule. |
| `02-wildfire-smoke-saskatchewan` | `wyvern_dragonette-003_20250531T173810_56fca26e_l2a` | Dragonette-003 | 31 | 2025-05-31 | Northern Saskatchewan, Canada (103.0°W, 55.1°N) | **Scene with real quality issues.** Captured during the late-May-2025 northern Saskatchewan wildfire complex; smoke and cloud cover 62.3% of valid pixels — past the QA-3 40% obstruction threshold → expected **retry**. |
| `03-copper-mine-chile` | `wyvern_dragonette-001_20240620T145630_2d5d0eef_l2a` | Dragonette-001 | 23 | 2024-06-20 | Atacama Desert, Chile (69.0°W, 24.4°S) | **Industrial scene.** Open-pit copper mining region, 0% cloud → expected to pass. Exercises the 23-band platform spec (Dragonette-001). |

## What's in each scene folder

Every folder contains the delivered artifacts for that acquisition:

| File | What it is |
|---|---|
| `stac_metadata.json` | Full STAC item (the catalog record for this scene) — source of platform, band list, cloud cover %, geometry, processing level |
| `preview.png` | RGB composite render of the scene (Wyvern's "Overview image") |
| `thumbnail.png` | Small RGB thumbnail |
| `data_mask.tiff` | 4-band usable-data mask: band 1 = clear, band 2 = cloud, band 3 = haze, band 4 = cloud-shadow (1 = present, 0 = absent, 255 = NoData) — produced by Wyvern's QA system |
| `pixel_quality_mask.tiff` | Per-band pixel quality flags (same band count as the image): 0 = no documented condition, 1 = interpolated pixel, 255 = NoData |

The `data_mask.tiff` + `pixel_quality_mask.tiff` + `stac_metadata.json` are the **inputs the triage agent
reads** (`agent/`); the previews are for humans (docs + dashboard).

## Deliberate scoping decision: no full-resolution band stack in this repo

Each scene's full hyperspectral product ("Cloud optimized GeoTiff") is a **2.2–3.1 GB** 23/31-band uint16
file — e.g. `wyvern_dragonette-003_20250319T000402_d5ebab06_l2a.tiff` is 3,498,438,408 bytes. The ODP host
advertises `accept-ranges: bytes` but ignores Range requests (returns HTTP 200 with the entire body), so the
COG cannot be partially read — mirroring all three would add ~8.5 GB to this repo.

We therefore keep the delivered companions (masks, previews, metadata) and link the full product in each
`stac_metadata.json` (`assets["Cloud optimized GeoTiff"]["href"]`). Consequence for the QA agent: rules that
need actual reflectance values (QA-6 reflectance bounds, QA-7 internal consistency) are implemented but
logged as **not assessable** on these scenes — the agent states exactly which rules it could and couldn't
evaluate. This mirrors a real production constraint: a QA layer can only certify what it can read.

## How the data was pulled

```python
# Browse the catalog
GET https://wyvern-odp.com/catalog.json                  # root
GET https://wyvern-odp.com/application/<name>/collection.json  # agriculture, disaster, mining, energy, …
# Each collection lists STAC items; each item lists its assets (above).
```

Scene selection was evidence-based, not visual: for each candidate, the data mask and pixel quality mask
were downloaded and reduced to numbers (cloud/haze %, interpolated pixels, mask coverage) before choosing.
See `docs/pipeline-walkthrough.md` for the full per-scene analysis.
