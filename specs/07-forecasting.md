# Modules 7–9: AI and forecasting

**Owner:** Person 3 (AI and forecasting). **Feeds:** the planner (Darve) and the frontend.

| Module | File | Does |
|---|---|---|
| 7 | `core/forecast.py` | weekly demand forecast per product, with an 80% range |
| 8 | `core/stockout.py` | when each material runs out and the last day to reorder |
| 9 | `core/explain.py` | plain-English (or Bahasa Melayu) explanations, optional free LLM |

**Done when:** `pytest -v` is all green (no internet or API key needed).

## Module 7: forecast

Input: `data/forecasting/sales_history.csv` + `calendar_events.csv`.

**Model:** one log-linear regression per product (numpy only):

`log(units) = trend + price + promo + school holiday + Ramadan + festival-week effects`

- Festival effects: a shared curve for "3, 2, 1 weeks before / festival week / week after",
  plus a per-festival adjustment that is shrunk towards the shared curve (ridge), because each
  festival appears only about twice in two years. This is how the model learns Raya > CNY > Deepavali.
- **Outliers:** fit once, flag weeks whose error is more than 3.5 robust standard deviations,
  refit without them. Catches the 4× corporate order on `COOKIE_BTR` 2025-04-28 but keeps real festive peaks.
- **Missing weeks** are skipped, not filled in (`KUIH_KELAPA` 2025-08-18). Both show up in `data_quality`.
- Future weeks get their holiday/festival features from the calendar, so the Deepavali 2026-11-08 rush is predicted.
- Range: `exp(prediction ± 1.28 × error std)` = 80% interval.

**Backtest** (in every response): train on all but the last 26 weeks, score on those 26.

| Product | Model error (MAPE) | Last-4-weeks average | Same week last year | 80% range hit rate |
|---|---|---|---|---|
| COOKIE_BTR | 6.8% | 18.9% | 31.2% | 77% |
| CURRY_PUFF | 5.3% | 13.9% | 19.3% | 81% |
| KUIH_KELAPA | 9.2% | 20.2% | 16.8% | 77% |

**Output** (one row per product per week), matching the agreed contract plus extra explanation fields:

```
week_start, product_id, forecast_units, lower_80, upper_80, change_vs_last_4_weeks_pct, drivers[]
```

- `forecast_to_orders(rows, scenario="forecast_units" | "upper_80")` → planned `Order`s due at the end of each week.
- `python -m core.forecast --weeks 4 --csv forecast.csv` writes the contract CSV.

## Module 8: stockout predictions

For each material, walk the stock forward day by day (working days only, from `planning_start`):

- Weekly demand = **larger of** the forecast and the confirmed orders due that week (orders are part of demand, not extra).
- Demand is spread evenly over the week's working days; the first week only counts days from `planning_start`.
- `stockout_date` = first day the stock cannot cover that day's use. `order_by = stockout_date − lead_time_days`.
- Run twice: **expected** (`forecast_units`) and **high demand** (`upper_80`).

| `status` | Meaning |
|---|---|
| `critical` | runs out before a delivery could arrive, even if ordered today |
| `reorder_now` | order-by date is within 2 days |
| `reorder_soon` | runs out within the horizon, still time |
| `watch` | only runs out in the high-demand scenario |
| `ok` | enough stock for the horizon |

`products_at_risk`: the first day each product can no longer be made, and which material stops it.
Like the planner, nothing is ordered: `recommended_order_qty` is a suggestion for the owner.

## Module 9: explanations

1. `build_facts(plan, forecast, stockout)`: a compact JSON of calculated numbers. The **only** input to any explanation.
2. Templates always produce: `summary`, one text per order, per forecast row and per at-risk material.
3. If a free key is set, an LLM rewrites `summary` as a short owner briefing (`source: "llm"`).
   `ask(question)` answers free-text questions, in English or Bahasa Melayu.
4. **Number guard:** every number in the LLM's text must appear in the facts (also allowing % and rounded forms).
   Otherwise the LLM text is thrown away and a `warning` says why. Network errors, quota limits or no key → templates.

### Free AI keys (pick one, put it in `.env`, see `.env.example`)

| Provider | Env var | Get a key | Default model |
|---|---|---|---|
| Groq | `GROQ_API_KEY` | https://console.groq.com/keys | `llama-3.3-70b-versatile` |
| Google Gemini | `GEMINI_API_KEY` | https://aistudio.google.com/apikey | `gemini-flash-lite-latest` |
| OpenRouter | `OPENROUTER_API_KEY` | https://openrouter.ai/keys | `meta-llama/llama-3.3-70b-instruct:free` |

All three are called through their OpenAI-compatible `/chat/completions` endpoint with `httpx`, so no extra SDK.
Set `LLM_MODEL` if a default model is retired. `LLM_API_KEY` + `LLM_BASE_URL` works with any other compatible provider.

## API

| Method + path | Returns |
|---|---|
| `GET /forecast/sample?weeks=4` | module 7 output with backtest and data-quality notes |
| `GET /stockout/sample?weeks=4` | module 8 output |
| `GET /insights/sample?weeks=4&language=en\|ms` | `{plan, forecast, stockout, explanations}` in one call |
| `POST /insights/ask` `{"question": "...", "language": "en"}` | `{answer, source, warnings}` |

`weeks` is 1–12. `/plan` and `/plan/sample` are unchanged.

## Note on the sample data

The sales history (~300 units/product/week) is much bigger than the 6 sample orders, and stock is sized for
the orders. So on the sample data every material shows as running out in 1–3 days. That is the correct answer
for those numbers; with real stock levels the statuses spread out.

## Think about (judges may ask)
- Why not let the LLM do the forecasting? (Numbers must be calculated and checkable; the backtest proves the model.)
- Why does the LLM only get pre-computed facts, and what stops it inventing numbers?
- What happens at the demo if the Wi-Fi or the free quota dies? (Templates, same numbers.)
