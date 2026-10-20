"""Production planner: decides the order sequence and checks materials, time and deadlines.

YOUR TASK: replace every `raise NotImplementedError` so `pytest tests/test_planner.py` passes.
Suggested order: working_hours_until -> production_hours -> edd_sequence / baseline_sequence
-> plan_orders -> build_baseline_plan / build_optimised_plan.

Rules the planner must follow:
  * Orders are processed one at a time in the given sequence on ONE production line.
  * An order is only produced if ALL its materials are available (use InventoryLedger).
    Otherwise it is INFEASIBLE: no materials consumed, no time slot, clock does not move.
  * A produced order starts when the previous produced order ends (clock starts at hour 0).
  * Produced orders are ON_TIME if end_hour <= hours_available_by_due, else LATE.
    LATE orders are still produced (they consume materials and time).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

from timed.inventory import InventoryLedger, build_recipe_index, material_cost, requirements_for  # noqa: F401
from timed.models import Capacity, Order, Product, ProductionInput

# Index matches date.weekday(): Monday == 0.
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class OrderStatus(str, Enum):
    ON_TIME = "on_time"
    LATE = "late"
    INFEASIBLE = "infeasible"


class ScheduledOrder(BaseModel):
    """Planner result for one order. Times are working hours counted from the planning start."""

    order_id: str
    product_id: str
    quantity: int
    due_date: date
    status: OrderStatus
    start_hour: float | None = None          # None when INFEASIBLE
    end_hour: float | None = None            # None when INFEASIBLE
    hours_available_by_due: float            # working_hours_until(capacity, due_date)
    materials_used: dict[str, float] = Field(default_factory=dict)     # empty when INFEASIBLE
    material_cost_rm: float = 0.0                                       # 0 when INFEASIBLE
    missing_materials: dict[str, float] = Field(default_factory=dict)  # only when INFEASIBLE
    reason: str                              # plain-English explanation for the user


class PlanResult(BaseModel):
    orders: list[ScheduledOrder]             # in the order they were processed
    remaining_stock: dict[str, float]        # material_id -> stock left after the plan
    hours_used: float                        # end hour of the last produced order (0 if none)


def working_hours_until(capacity: Capacity, due_date: date) -> float:
    """Working hours from planning_start up to the END of due_date (both days inclusive).

    Only days whose weekday name is in capacity.working_days count.
    Returns 0 if due_date is before planning_start.
    Hint: loop over days with datetime.timedelta(days=i).
    """
    raise NotImplementedError


def production_hours(order: Order, products: Mapping[str, Product]) -> float:
    """Hours needed to make the order = quantity / units_per_hour."""
    raise NotImplementedError


def edd_sequence(orders: Sequence[Order]) -> list[Order]:
    """Earliest-Due-Date first; ties broken by order_id so the result is deterministic."""
    raise NotImplementedError


def baseline_sequence(orders: Sequence[Order]) -> list[Order]:
    """Baseline = first come, first served: keep the orders in the order they arrived."""
    raise NotImplementedError


def plan_orders(data: ProductionInput, sequence: Sequence[Order]) -> PlanResult:
    """Process orders in `sequence`, allocating materials and time. See module docstring for rules.

    Steps per order:
      1. needs = requirements_for(order.product_id, order.quantity, recipe_index)
      2. missing = ledger.missing_for(needs) -> if any: INFEASIBLE, reason names each short material
      3. else ledger.allocate(needs), start = clock, end = clock + production_hours, clock = end
      4. ON_TIME or LATE by comparing end to working_hours_until(capacity, order.due_date);
         a LATE reason must contain the word "late"
    """
    raise NotImplementedError


def build_baseline_plan(data: ProductionInput) -> PlanResult:
    """Plan using baseline_sequence."""
    raise NotImplementedError


def build_optimised_plan(data: ProductionInput) -> PlanResult:
    """Plan using edd_sequence."""
    raise NotImplementedError
