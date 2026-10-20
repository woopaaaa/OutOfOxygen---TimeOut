"""Deterministic inventory, shortage and cost calculations.

Formulas (per material m):
    required[m]        = sum over orders o of  o.quantity * recipe[o.product][m]
    material_cost      = sum over m of  required[m] * unit_cost[m]
    production_short[m]= max(0, required[m] - stock[m])                 # blocks production
    purchase_qty[m]    = max(0, required[m] + min_stock[m] - stock[m])  # also restores safety stock
    purchase_cost[m]   = purchase_qty[m] * unit_cost[m]
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

from pydantic import BaseModel

from timed.models import Material, Order, RecipeLine

QTY_DP = 4   # rounding for quantities (avoids 0.30000000000000004 in output)
MONEY_DP = 2

Requirements = dict[str, float]  # material_id -> quantity


class ShortageLine(BaseModel):
    material_id: str
    name: str
    unit: str
    required: float
    in_stock: float
    min_stock: float
    production_shortage: float
    purchase_quantity: float
    unit_cost_rm: float
    purchase_cost_rm: float
    lead_time_days: int | None


def build_recipe_index(recipes: Iterable[RecipeLine]) -> dict[str, dict[str, float]]:
    """product_id -> {material_id: quantity_per_unit}."""
    index: dict[str, dict[str, float]] = defaultdict(dict)
    for line in recipes:
        index[line.product_id][line.material_id] = line.quantity_per_unit
    return dict(index)


def requirements_for(product_id: str, quantity: float, recipe_index: Mapping[str, Mapping[str, float]]) -> Requirements:
    """Materials needed to make ``quantity`` units of one product."""
    if product_id not in recipe_index:
        raise KeyError(f"No recipe for product '{product_id}'")
    return {mid: round(per_unit * quantity, QTY_DP) for mid, per_unit in recipe_index[product_id].items()}


def total_requirements(orders: Iterable[Order], recipe_index: Mapping[str, Mapping[str, float]]) -> Requirements:
    """Aggregate material requirements across orders."""
    totals: dict[str, float] = defaultdict(float)
    for order in orders:
        for mid, qty in requirements_for(order.product_id, order.quantity, recipe_index).items():
            totals[mid] += qty
    return {mid: round(qty, QTY_DP) for mid, qty in totals.items()}


def material_cost(requirements: Mapping[str, float], materials: Mapping[str, Material]) -> float:
    """Cost (RM) of consuming the given materials at unit cost."""
    return round(sum(qty * materials[mid].unit_cost_rm for mid, qty in requirements.items()), MONEY_DP)


def shortage_report(requirements: Mapping[str, float], materials: Mapping[str, Material]) -> list[ShortageLine]:
    """Per-material shortage and purchase suggestion. Only materials needing a purchase are returned."""
    lines: list[ShortageLine] = []
    for mid in sorted(requirements):
        material = materials[mid]
        required = requirements[mid]
        production_shortage = round(max(0.0, required - material.quantity_in_stock), QTY_DP)
        purchase_qty = round(max(0.0, required + material.min_stock - material.quantity_in_stock), QTY_DP)
        if purchase_qty == 0:
            continue
        lines.append(
            ShortageLine(
                material_id=mid,
                name=material.name,
                unit=material.unit,
                required=required,
                in_stock=material.quantity_in_stock,
                min_stock=material.min_stock,
                production_shortage=production_shortage,
                purchase_quantity=purchase_qty,
                unit_cost_rm=material.unit_cost_rm,
                purchase_cost_rm=round(purchase_qty * material.unit_cost_rm, MONEY_DP),
                lead_time_days=material.lead_time_days,
            )
        )
    return lines


class InventoryLedger:
    """Running stock balance used while allocating orders.

    ``allocate`` is all-or-nothing: an order either gets every material it needs
    or nothing is deducted, so stock is never double-counted or partially consumed.
    """

    def __init__(self, materials: Iterable[Material]) -> None:
        self._available: dict[str, float] = {m.material_id: m.quantity_in_stock for m in materials}

    def available(self, material_id: str) -> float:
        return self._available[material_id]

    def snapshot(self) -> dict[str, float]:
        return dict(self._available)

    def missing_for(self, needs: Mapping[str, float]) -> Requirements:
        """Materials (and amounts) that current stock cannot cover."""
        return {
            mid: round(qty - self._available[mid], QTY_DP)
            for mid, qty in needs.items()
            if qty > self._available[mid] + 1e-9
        }

    def can_allocate(self, needs: Mapping[str, float]) -> bool:
        return not self.missing_for(needs)

    def allocate(self, needs: Mapping[str, float]) -> bool:
        """Deduct ``needs`` if fully available. Returns True on success, False (no change) otherwise."""
        if not self.can_allocate(needs):
            return False
        for mid, qty in needs.items():
            self._available[mid] = round(self._available[mid] - qty, QTY_DP)
        return True
