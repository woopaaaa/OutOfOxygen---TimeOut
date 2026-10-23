# Module 5: `core/metrics.py` (before vs after numbers)

**Goal:** turn a plan into a few honest numbers, and compare the **baseline** (first come, first served)
with the **optimised** plan (earliest due date first). These are the "measurable benefit" numbers for
the pitch. The Domain 2 rubric (Clarity, 20%) asks for one, and the rules forbid making numbers up.

**Done when:** `pytest tests/test_metrics.py -v` is all green, **and** `tests/test_api.py` passes again
after you plug the metrics into `build_response` (see Part C).

## Worked example (the A/B factory from module 4)

Orders: **A** = 70 units due Fri (7 h), **B** = 20 units due Mon (2 h). Material costs RM 2/unit.
Capacity: Mon 19 Oct start, Mon–Fri, 8 h/day.

| Metric | How | Baseline | Optimised |
|---|---|---|---|
| `orders_total` | number of schedule lines | 2 | 2 |
| `orders_on_time` | lines with status `on_time` | 1 | 2 |
| `orders_late` | lines with status `late` | 1 | 0 |
| `orders_infeasible` | lines with status `infeasible` | 0 | 0 |
| `on_time_rate` | on_time ÷ total, rounded to 2 | 0.5 | 1.0 |
| `total_material_cost_rm` | sum of every line's `material_cost_rm`, rounded to 2 | 180.0 | 180.0 |
| `hours_used` | the plan's `hours_used` | 9 | 9 |
| `hours_available` | `working_hours_until(capacity, latest due date of all orders)` | 40 | 40 |
| `utilisation` | hours_used ÷ hours_available, rounded to 2 (0 if available is 0) | 0.23 | 0.23 |

The pitch sentence this gives: *"On the same orders and stock, Timed's plan raised on-time delivery
from 50% to 100% at the same material cost."* Every number is calculated.

## Part A: `plan_metrics(plan, data)`

Input: a plan dict (what `plan_orders` returns) and the `ProductionInput` it was made from.
Output: a dict with exactly the 9 keys in the table.

## Part B: `compare_plans(data)`

Returns `{"baseline": plan_metrics(<baseline plan>, data), "optimised": plan_metrics(<optimised plan>, data)}`.

## Part C: plug it into the API

In `core/api.py`, replace `"metrics": None` with `compare_plans(data)`.
`tests/test_api.py` now expects real metrics, so it fails until you do this.

## Tools you already have
`build_baseline_plan`, `build_optimised_plan`, `working_hours_until` (module 4), `sum`, `max`, `round`,
and list comprehensions with an `if`.

## Think about (judges may ask)
- Why measure against a baseline at all, instead of just showing the optimised plan?
- Utilisation is low in the sample data (the factory has spare hours). Is that good or bad news for the owner?
