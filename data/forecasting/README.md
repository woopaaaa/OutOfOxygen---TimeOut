# Forecasting sample data — ILLUSTRATIVE ONLY

Synthetic weekly sales for the fictional **Kuih Mesra Sdn Bhd**, built for the AI/forecasting teammate.
Generated with fixed rules plus random noise (seeded), so it is reproducible. **Not real sales.**
Festive and school-holiday dates are approximate. Check the official calendars before using real data.

## Files

### `sales_history.csv`: 106 weeks × 3 products (2024-10-07 → 2026-10-12)
| Column | Meaning |
|---|---|
| `week_start` | Monday of the sales week (ISO date) |
| `product_id` | Matches `data/products.csv` |
| `units_sold` | Units sold that week (target to forecast) |
| `avg_price_rm` | Average selling price that week (RM) |
| `promo` | 1 if a promotion ran (10% off) |
| `school_holiday` | 1 if the week overlaps a school holiday |
| `ramadan` | 1 if the week overlaps Ramadan |
| `festive_event` | Nearest festival within −3…+1 weeks, else blank |
| `weeks_to_event` | Offset from that festival's week (−3 = three weeks before) |

### `calendar_events.csv`
Festivals, Ramadan, and school holiday start/end dates, **including future dates** (e.g. Deepavali 2026-11-08), so the forecast can use them as features.

## Patterns built into the data (use these to check the model learns something real)
| Pattern | Products | Effect |
|---|---|---|
| Growth trend | all | about +16% per year |
| Festive gift-box rush | cookies, coconut biscuits | demand rises 3 weeks before a festival (peaks the week before, about 2× for Deepavali and higher for Raya), then drops below normal the week after |
| Festival strength | — | Raya > CNY > Deepavali > Christmas > Raya Haji |
| Ramadan bazaars | curry puffs | +35% during Ramadan |
| School holidays | curry puffs | −25% (school canteen orders stop) |
| Price increase 2025-07-07 | butter cookies | RM18.00 → RM19.50, about −6% demand |
| Promotions | all | about 8% of weeks, +25% demand |
| Noise | all | ±8% random |

## Deliberate data-quality issues (the forecaster should handle these)
1. **Missing week:** `KUIH_KELAPA` has no row for `2025-08-18`.
2. **Outlier:** `COOKIE_BTR` on `2025-04-28` is about 4× normal (one-off corporate bulk order). It should not inflate the forecast.

## Interface contract: forecasting → optimisation
The planner takes `Order` records (see `specs/01-models.md`). The forecast should output one row per product per future week:

```
week_start,product_id,forecast_units,lower_80,upper_80
2026-10-19,COOKIE_BTR,<number>,<number>,<number>
```

The optimisation module turns each row into a planned `Order` (due date = end of that week, quantity = `forecast_units`) and can run the upper bound as a "high demand" scenario. **Agree this format with the optimisation owner (Darve) before building.**

Good test for the demo: forecast the 4 weeks before **Deepavali 2026-11-08**. A good model should predict the gift-box rush.
