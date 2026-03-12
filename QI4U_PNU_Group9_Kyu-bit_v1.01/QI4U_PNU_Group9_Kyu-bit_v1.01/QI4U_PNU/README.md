# Agricultural Optimization (QUBO) — Updated Version

## Overview
This project solves an agricultural planting optimization problem using a QUBO formulation.  
It visualizes soil quality on a grid and searches for planting placements that satisfy spacing constraints while improving objective scores.

## What’s New in This Version
- Added additional **Korean inline comments** while reviewing and interpreting the existing code (to improve readability and maintainability).
- Extended the workflow to run optimization across **all crops** (instead of a single crop per run).
- Aggregated per-crop results and **normalized the key metrics**, then displayed them in a **table format** for easier comparison.

## Outputs
Depending on your configuration, the program can produce:
- A soil quality heatmap with selected planting points overlaid
- Per-crop summary metrics (e.g., density, occupancy, energy per plant)
- A normalized comparison table across crops

## Notes
- Normalization requires global min/max values across all crops, so metrics are collected first and normalized after all crop runs are complete.
- If you modify spacing rules or candidate step sizes, results may change significantly. Keep parameters consistent when comparing crops.