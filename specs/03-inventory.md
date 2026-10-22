# Module 3: `core/inventory.py` (materials, shortages, cost)

**Goal:** answer three questions with exact maths, no guessing:
1. How much of each material do these orders need?
2. Is there enough in stock? If not, how much must we buy, and what will it cost?
3. While planning, how do we hand out stock to orders **without counting the same flour twice**?

**Done when:** `pytest tests/test_inventory.py -v` is all green, and all other tests still pass.

## Worked example (from `data/`)

Order ORD-001: **60 boxes of butter cookies**. One box needs (from `recipes.csv`):
0.40 kg flour, 0.15 kg sugar, 0.12 kg butter, 2 eggs, 1 packaging box.

| Material | Per box | × 60 boxes | Unit cost (RM) | Cost (RM) |
|---|---|---|---|---|
| FLOUR | 0.40 kg | 24 kg | 3.20 | 76.80 |
| SUGAR | 0.15 kg | 9 kg | 2.85 | 25.65 |
| BUTTER | 0.12 kg | 7.2 kg | 28.00 | 201.60 |
| EGG | 2 pcs | 120 pcs | 0.45 | 54.00 |
| PACK | 1 pc | 60 pcs | 0.60 | 36.00 |
| | | | **Total** | **394.05** |

Now suppose all orders together need **20 kg butter**. Stock is 15 kg, minimum stock is 5 kg:
- **shortage** = 20 − 15 = **5 kg** → production is blocked by 5 kg
- **purchase quantity** = 20 + 5 − 15 = **10 kg** → buy enough to also refill the safety stock
- **purchase cost** = 10 × 28.00 = **RM 280.00**

## Part A: calculations (functions)

| Function | Input | Output |
|---|---|---|
| `build_recipe_index(recipes)` | list of `RecipeLine` | dict: product_id → {material_id: quantity_per_unit} |
| `requirements_for(product_id, quantity, recipe_index)` | one product and how many | dict: material_id → amount needed |
| `total_requirements(orders, recipe_index)` | list of `Order` | dict: material_id → total amount for **all** orders |
| `material_cost(requirements, materials)` | needs dict, and materials as dict material_id → `Material` | total RM, rounded to 2 decimals |
| `material_report(requirements, materials)` | same as above | list of dicts, one per material needed (see below) |

`material_report` returns one dict per material in `requirements`, sorted by `material_id`,
with exactly the keys of **MaterialLine** in `specs/output-contract.md`:
`material_id, name, unit, required, in_stock, shortage, purchase_quantity, unit_cost_rm, purchase_cost_rm, lead_time_days`.

Formulas:
- `shortage = max(0, required − in_stock)`
- `purchase_quantity = max(0, required + min_stock − in_stock)`
- `purchase_cost_rm = purchase_quantity × unit_cost_rm`, rounded to 2 decimals

Rounding: quantities to **4** decimals (so 0.1 + 0.2 shows as 0.3, not 0.30000000000000004), money to **2**.

`requirements_for` must raise `KeyError` if the product has no recipe.

## Part B: `InventoryLedger` (a class)

The planner will hand out materials to orders one by one. The ledger keeps the **running stock**.

| Method | Does |
|---|---|
| `InventoryLedger(materials)` | starts with each material's `quantity_in_stock` |
| `available(material_id)` | how much is left now |
| `missing_for(needs)` | dict of only the materials that are short, and by how much (empty dict = all fine) |
| `allocate(needs)` | if **everything** is available: subtract it all and return `True`. If **anything** is short: change **nothing** and return `False` |
| `snapshot()` | a **copy** of the current stock as a dict (changing the copy must not change the ledger) |

Example: butter stock 15 kg.
- Order A needs 10 kg → `allocate` returns `True`, butter left = 5 kg.
- Order B needs 10 kg → only 5 left → returns `False`, butter **stays** 5 kg. (Not −5. Not 0.)
- Order C needs 3 kg flour **and** 999 kg chicken → returns `False`, and the flour is **not** taken either.

That last rule is called **all-or-nothing**. Why does it matter? If you took the flour anyway,
a later order that only needs flour might be wrongly marked as impossible.

## Think about (judges may ask)
- Why does `purchase_quantity` include `min_stock` but `shortage` doesn't?
- Why does the ledger return a copy in `snapshot()`?
