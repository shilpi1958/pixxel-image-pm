# Data — 3 real Wyvern hyperspectral scenes

- Real imagery from [Wyvern's Open Data Program](https://wyvern.space/open-data/) via their public STAC catalog
- No synthetic data anywhere in this repo
- **Catalog root:** <https://wyvern-odp.com/catalog.json> (STAC 1.0.0)
- Browsable at <https://opendata.wyvern.space/>
- **License:** [CC BY 4.0](https://www.wyvern.space/blog/wyvern-launches-open-data-program-to-provide-unrestricted-hyperspectral-data-access), free with attribution to Wyvern
- Individual STAC items carry a stale `"proprietary"` field — the program announcement is authoritative
- **Processing level:** all three scenes are L2A surface reflectance
- L1B radiance isn't offered for these scenes in the ODP

## The three scenes

| Folder | Scene ID | Platform | Bands | Date (UTC) | Location | Why picked |
|---|---|---|---|---|---|---|
| `01-clean-cropfield-australia` | `wyvern_dragonette-003_20250319T000402_d5ebab06_l2a` | Dragonette-003 | 31 | 2025-03-19 | Victoria, Australia | Clean scene — 0% cloud/haze, 100% clear, 0 interpolated pixels → expected pass |
| `02-wildfire-smoke-saskatchewan` | `wyvern_dragonette-003_20250531T173810_56fca26e_l2a` | Dragonette-003 | 31 | 2025-05-31 | N. Saskatchewan, Canada | Real quality issues — 62.3% cloud+smoke, past QA-3's 40% threshold → expected retry |
| `03-copper-mine-chile` | `wyvern_dragonette-001_20240620T145630_2d5d0eef_l2a` | Dragonette-001 | 23 | 2024-06-20 | Atacama Desert, Chile | Industrial scene, 0% cloud → expected pass; exercises the 23-band platform spec |

## What's in each scene folder

| File | What it is |
|---|---|
| `stac_metadata.json` | STAC item — platform, band list, cloud cover %, geometry, processing level |
| `preview.png` / `thumbnail.png` | RGB renders |
| `data_mask.tiff` | 4-band usable-data mask: clear / cloud / haze / cloud-shadow (1 present, 0 absent, 255 NoData) |
| `pixel_quality_mask.tiff` | Per-band quality flags: 0 ok, 1 interpolated, 255 NoData |

- The mask files + `stac_metadata.json` are what the rule engine reads (`agent/`); previews are for humans (dashboard)

### Two masks, two different notions of "band"

| | `data_mask.tiff` | `pixel_quality_mask.tiff` |
|---|---|---|
| Answers | Is atmosphere blocking the view? | Which pixels, per wavelength, were filled in by interpolation? |
| Layer count | Always 4 — fixed | Matches the scene's real band count (31 or 23) |
| Layer meaning | 1 clear, 2 cloud, 3 haze, 4 cloud-shadow | One layer per wavelength |
| Cause of a flag | Weather / atmosphere / lighting | Interpolation of missing pixel rows (per Wyvern's release notes) |
| PRD rule fed | QA-2, QA-3 | QA-4 |

- `data_mask.tiff` stays at 4 layers — it's a derived classification *across* bands
- `pixel_quality_mask.tiff` tracks each wavelength independently
- That's why interpolation can affect some bands and not others

## Scoping: no full-resolution band stack mirrored by default

- Each full hyperspectral product (COG) is 2.2–3.1 GB, 23/31-band uint16 — e.g. one file alone is 3,498,438,408 bytes
- The ODP host ignores Range requests (always returns the full body), so partial reads aren't possible — mirroring all three would add ~8.5 GB
- The repo keeps the delivered companions instead (masks, previews, metadata)
- The full product is linked via `stac_metadata.json`'s `assets["Cloud optimized GeoTiff"]["href"]`
- QA-6/QA-7 log as **not assessable** whenever no band stack is supplied
- That's a per-run limitation, not a claim these rules can never run
- **Exception:** `03-copper-mine-chile`'s stack was pulled and QA-6/QA-7 run against real reflectance
- See [`03-copper-mine-chile/band_stack_analysis.json`](03-copper-mine-chile/band_stack_analysis.json) and the [dashboard](../dashboard/) for the finding
- Mirrors a real production constraint: a QA layer can only certify what it can read

## How the data was pulled

```python
GET https://wyvern-odp.com/catalog.json                        # root
GET https://wyvern-odp.com/application/<name>/collection.json  # agriculture, disaster, mining, energy, …
```

- Scene selection was evidence-based, not visual
- Masks were pulled and reduced to numbers (cloud/haze %, interpolated pixels, mask coverage) before selection
- See the [dashboard](../dashboard/) for the full per-scene analysis
