# IPR PM Assignment – Submission

Nov 7, 2026 · @Sj

## Deliverables

| # | Deliverable | Where |
| --- | --- | --- |
| 1 | 2-page note: what is happening in the pipeline, plus answers to questions A–F | [IPR Pipeline Health – 2-Page Note](https://claude.ai/artifact/KrdGb5BH8VL27FtyKeSyhM) |
| 2 | Top 5 daily metrics, with numerator and denominator | [2-page note, "Top 5 daily metrics"](https://claude.ai/artifact/KrdGb5BH8VL27FtyKeSyhM); live on the dashboard |
| 3 | Dashboard: views for the IPR lead, QA/QC, Engineering and Customer Success, filtered by week, satellite, bandset, priority and customer | [IPR Pipeline Dashboard](https://claude.ai/artifact/Mhwa4vGycz9VmhNg5EoQaE) |
| 4 | 2-week plan for 2 engineers and 1 QA/QC person | [IPR 2-Week Plan](https://claude.ai/artifact/7TYRU23LDK93ek3b6BkZGc) |
| 5a | Internal update to Engineering, IPR and QA/QC | [IPR Internal Update](https://claude.ai/artifact/25V8313piwHiLKw7AvQ37m) |
| 5b | Customer-safe update to Customer Success for a delayed high-priority image (UrbanAtlas P0s) | [IPR Customer-Safe Update](https://claude.ai/artifact/JD7iAD5vj794xZMk5ZnhaA) |

**Supporting material:**

- [IPR Data Cleaning Rules](https://claude.ai/artifact/55PXGiyx3VkYovwm47s61s): every cleaning decision, with counts.
- **IPR\_Cleaned\_Data.xlsx** (attached): the cleaned data, one row per image attempt. It includes a column guide and a log of every changed cell.

## Key assumptions

- **One row per image:** the latest valid attempt. 136 export rows → 95 images, 89 of them processable.
- **Delivered** = passed QC and uploaded. Uploaded without a QC pass doesn't count.
- **SLA** runs from acquisition, locked to the attempt-1 priority.
- **"Now"** = 30 Jun 2026 16:06 UTC, the latest timestamp in the export (it has no pull time).
- **Step targets** (share of the SLA window) are my proposal, still to be agreed with Engineering and QA.
