# Module 1 — `core/models.py` (input data models)

**Goal:** define what valid input looks like, and reject bad input *before* any calculation runs.
Every later module trusts these models, so this is the foundation.

**Done when:** `pytest tests/test_models.py -v` is all green.

## What to do before start
1. Create the folder `core/` (next to `data/` and `tests/`) with an empty `__init__.py` inside.
   That file turns the folder into a Python package so `from core.models import Order` works.
2. Read the Pydantic v2 basics: `BaseModel`, `Field(gt=0, ge=0, min_length=1)`, `@model_validator(mode="after")`.
   Docs: https://docs.pydantic.dev/latest/concepts/models/ and /concepts/validators/

## Models to write

All money is RM. All quantities are in the item's own unit (kg, pcs, box).

| Model | Field | Type | Rule |
|---|---|---|---|
| `Material` | `material_id` | str | not empty |
| | `name`, `unit` | str | |
| | `quantity_in_stock` | float | ≥ 0 |
| | `unit_cost_rm` | float | ≥ 0 |
| | `min_stock` | float | ≥ 0, default 0 |
| | `lead_time_days` | int or None | ≥ 0, default None (= unknown) |
| `Product` | `product_id` | str | not empty |
| | `name`, `unit` | str | |
| | `units_per_hour` | float | > 0 |
| `RecipeLine` | `product_id`, `material_id` | str | |
| | `quantity_per_unit` | float | > 0 (material for ONE unit of product) |
| `Order` | `order_id` | str | not empty |
| | `customer`, `product_id` | str | |
| | `quantity` | int | > 0 |
| | `due_date` | `datetime.date` | |
| `Capacity` | `planning_start` | date | |
| | `hours_per_day` | float | > 0 and ≤ 24 |
| | `working_days` | list of `"Mon"`…`"Sun"` | at least 1; anything else rejected (hint: `typing.Literal`) |
| `ProductionInput` | `materials`, `products`, `recipes`, `orders` | lists of the above | each at least 1 item |
| | `capacity` | `Capacity` | |

## Cross-checks in `ProductionInput`

Single-field rules can't catch these — they need the whole input. Use one `@model_validator(mode="after")`,
collect **all** problems into a list, then raise one `ValueError` joining them with `"; "`
(so the user sees every problem at once, not one per attempt).

Error messages must contain these exact phrases:

| Problem | Message must contain |
|---|---|
| Same id twice in materials/products/orders | `Duplicate material_id` / `Duplicate product_id` / `Duplicate order_id` |
| Recipe uses a product that doesn't exist | `unknown product 'X'` |
| Recipe uses a material that doesn't exist | `unknown material 'X'` |
| Same (product, material) recipe line twice | `Duplicate recipe line` |
| Order for a product that doesn't exist | `unknown product 'X'` |
| Order for a product that exists but has no recipe | `Missing information` and `has no recipe` |

## Think about (judges may ask)
- Why reject bad data instead of skipping it? → a plan built on silently dropped data looks valid but isn't.
- Why `quantity: int` for orders but `float` for materials?
