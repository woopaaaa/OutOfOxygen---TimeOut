# Output contract: what the optimisation engine returns

**For:** backend and frontend teammates. **Owner:** Darve (optimisation & analytics).
**Status:** draft, agreed shape only. The engine is still being built. Build your screens against
`specs/output-example.json` now, then swap in the real response when the API is ready.

## Where it fits in the Domain 2 journey

| Journey step | Who | What |
|---|---|---|
| 1. Trigger | backend | new order arrives / owner clicks "Plan production" |
| 2. Connected data | engine (`core/loader.py`) | orders, stock, recipes, capacity |
| 3. Decision logic | **engine (this contract)** | schedule, shortages, purchase request, metrics |
| 4. Human approval | backend + frontend | Owner role approves `purchase_request` (Staff can only view) |
| 5. Outcome + log | backend | approved purchase order + entry in activity log |

The engine **never** approves or sends anything. It only recommends. `purchase_request.status`
always starts as `"pending_approval"`.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `generated_at` | ISO datetime string | when the plan was calculated |
| `planning_start` | ISO date | first day of the plan |
| `schedule` | list of **ScheduleLine** | every order, in the order it was planned |
| `material_requirements` | list of **MaterialLine** | every material the planned orders use |
| `purchase_request` | **PurchaseRequest** | what to buy; needs approval |
| `metrics` | **Metrics** | baseline vs optimised numbers |
| `warnings` | list of strings | problems a human should look at |
| `assumptions` | list of strings | simplifications the engine made |

### ScheduleLine
| Field | Type | Notes |
|---|---|---|
| `order_id`, `customer`, `product_id` | string | from the order |
| `quantity` | int | |
| `due_date` | ISO date | |
| `status` | `"on_time"` / `"late"` / `"infeasible"` | |
| `start_hour`, `end_hour` | number or `null` | working hours from `planning_start`; `null` if infeasible |
| `material_cost_rm` | number | 0 if infeasible |
| `reason` | string | plain-English explanation, show it to the user |

### MaterialLine
| Field | Type | Notes |
|---|---|---|
| `material_id`, `name`, `unit` | string | |
| `required` | number | total needed by all orders |
| `in_stock` | number | |
| `shortage` | number | how much production is blocked by (0 if enough) |
| `purchase_quantity` | number | `required + min_stock − in_stock`, never below 0 |
| `unit_cost_rm`, `purchase_cost_rm` | number | RM, 2 decimals |
| `lead_time_days` | int or `null` | `null` = supplier lead time unknown |

### PurchaseRequest
| Field | Type | Notes |
|---|---|---|
| `status` | `"pending_approval"` | backend changes it after the Owner decides |
| `requires_role` | `"owner"` | who may approve |
| `lines` | list of `{material_id, name, unit, quantity, unit_cost_rm, cost_rm}` | only materials with `purchase_quantity > 0` |
| `total_cost_rm` | number | sum of `cost_rm` |

### Metrics
`baseline` (first come, first served) and `optimised` (earliest due date first), each with:
`orders_total`, `orders_on_time`, `orders_late`, `orders_infeasible`, `on_time_rate` (0–1),
`total_material_cost_rm`, `hours_used`, `hours_available`, `utilisation` (0–1).

## Rules
- Money in RM, rounded to 2 decimals. Quantities in the material's own unit.
- Every order appears in `schedule` exactly once.
- Numbers are **calculated, never invented**. If data is missing, the engine adds a `warning` instead of guessing.
