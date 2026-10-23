# Module 4: `core/planner.py` (decide the production plan)

**Goal:** given the orders, stock, recipes and capacity, decide **in what order to make things**,
and for every order say **on time**, **late** or **infeasible** (impossible), with a reason.
This is the **decision logic** step of the Domain 2 journey.

**Done when:** `pytest tests/test_planner.py -v` is all green, and all other tests still pass.

## The rules (read these first)

1. **One production line.** Orders are made one after another, never at the same time.
2. **The clock** counts **working hours** from the planning start. It starts at hour 0.
3. Orders are handled in a given **sequence** (see the two sequences below).
4. For each order:
   - if the ledger can't supply **all** its materials → **infeasible**. It gets no time slot, uses no materials, and **the clock does not move**.
   - otherwise → take the materials (`allocate`), start = clock, end = clock + production hours, then move the clock to end.
     - end ≤ working hours available by the due date → **on time**
     - end > that → **late** (still made: it uses materials and time)

## Worked example: working hours until a due date

Sample capacity: starts **Wed 21 Oct 2026**, works **Mon–Sat**, **8 h/day**.

| Due date | Working days from Wed 21 up to and including the due date | Hours |
|---|---|---|
| Thu 22 Oct | Wed, Thu | 16 |
| Fri 23 Oct | Wed, Thu, Fri | 24 |
| Sat 24 Oct | Wed–Sat | 32 |
| Mon 26 Oct | Wed–Sat, (Sun skipped), Mon | 40 |
| Tue 20 Oct | before the start | 0 |

## Worked example: planning two orders

Factory: product P makes **10 units/hour**, needs 1 kg of material M per unit, stock M = 100 kg.
Capacity: Mon 19 Oct start, Mon–Fri, 8 h/day.

Orders (in arrival order): **A** = 70 units due Fri (7 h of work), **B** = 20 units due Mon (2 h).

| Sequence | Order | Start → end | Hours available by due | Status |
|---|---|---|---|---|
| **Baseline** (arrival order) | A | 0 → 7 | 40 | on time |
| | B | 7 → 9 | 8 | **late** |
| **Optimised** (earliest due first) | B | 0 → 2 | 8 | on time |
| | A | 2 → 9 | 40 | on time |

Same orders, same stock. Only the **order of work** changed, and one late order became on time.
That is the improvement your pitch will measure.

## What to write

| Name | Input | Output |
|---|---|---|
| `working_hours_until(capacity, due_date)` | `Capacity`, a date | working hours from the start up to the **end** of the due date |
| `production_hours(order, products)` | an `Order`, dict product_id → `Product` | `quantity ÷ units_per_hour` |
| `edd_sequence(orders)` | list of `Order` | a **new** list sorted by due date, ties broken by `order_id` |
| `baseline_sequence(orders)` | list of `Order` | a **new** list in the same (arrival) order |
| `plan_orders(data, sequence)` | `ProductionInput`, list of `Order` | a plan dict (below) |
| `build_baseline_plan(data)` | `ProductionInput` | `plan_orders` with the baseline sequence |
| `build_optimised_plan(data)` | `ProductionInput` | `plan_orders` with the EDD sequence |

### The plan dict that `plan_orders` returns

| Key | Value |
|---|---|
| `"schedule"` | list of schedule-line dicts, **in the order they were processed** |
| `"remaining_stock"` | the ledger's `snapshot()` at the end |
| `"hours_used"` | the clock at the end (0 if nothing was made) |

Each **schedule line** is a dict with these keys (the same as in `specs/output-contract.md`, plus `missing_materials`):

| Key | On time / late | Infeasible |
|---|---|---|
| `order_id`, `customer`, `product_id`, `quantity`, `due_date` | from the order (`due_date` stays a `date`) | same |
| `status` | `"on_time"` or `"late"` | `"infeasible"` |
| `start_hour`, `end_hour` | numbers, rounded to 2 | `None` |
| `material_cost_rm` | `material_cost(...)` of what it used | `0` |
| `missing_materials` | `{}` | the ledger's `missing_for(...)` result |
| `reason` | plain English. A late reason **must contain the word "late"** | plain English that **names each short material by its name** |

## Tools you already have
`build_recipe_index`, `requirements_for`, `material_cost`, `InventoryLedger` from module 3.
New: `datetime.timedelta(days=1)` to step from one day to the next, and `date.weekday()`
(Monday = 0 … Sunday = 6) to find the weekday name.

## Think about (judges may ask)
- Why does an infeasible order not move the clock?
- Earliest-due-date is a **simple rule**, not a perfect optimiser. When could it still give a bad plan?
  (Hint: what if a big late order uses up the butter a later small order needed?)
