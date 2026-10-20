"""Tests for timed/planner.py — make these pass.

Most tests use a tiny hand-made factory so every expected number can be checked by hand:
  * one product P, made at 10 units/hour
  * one material M, 100 kg in stock, RM2/kg, recipe = 1 kg per unit
  * planning starts Monday 2026-10-19, 8 h/day, Mon-Fri
"""

from datetime import date

import pytest

from timed.loader import load_production_input
from timed.models import Order, ProductionInput
from timed.planner import (
    OrderStatus,
    baseline_sequence,
    build_baseline_plan,
    build_optimised_plan,
    edd_sequence,
    plan_orders,
    production_hours,
    working_hours_until,
)

MON = date(2026, 10, 19)
FRI = date(2026, 10, 23)


def _order(oid: str, qty: int, due: date = FRI) -> Order:
    return Order(order_id=oid, customer="Test", product_id="P", quantity=qty, due_date=due)


def _factory(orders: list[Order]) -> ProductionInput:
    return ProductionInput(
        materials=[{"material_id": "M", "name": "Mat", "unit": "kg", "quantity_in_stock": 100, "unit_cost_rm": 2.0}],
        products=[{"product_id": "P", "name": "Prod", "unit": "box", "units_per_hour": 10}],
        recipes=[{"product_id": "P", "material_id": "M", "quantity_per_unit": 1}],
        orders=orders,
        capacity={"planning_start": MON, "hours_per_day": 8, "working_days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
    )


# ---------- 1. capacity helpers ----------

@pytest.mark.parametrize(
    ("due", "expected_hours"),
    [
        (date(2026, 10, 19), 8),   # due on the start day: that whole day counts
        (date(2026, 10, 23), 40),  # Mon..Fri
        (date(2026, 10, 25), 40),  # weekend adds nothing
        (date(2026, 10, 26), 48),  # next Monday
        (date(2026, 10, 18), 0),   # due before planning starts
    ],
)
def test_working_hours_until(due, expected_hours):
    capacity = _factory([_order("A", 1)]).capacity
    assert working_hours_until(capacity, due) == expected_hours


def test_production_hours():
    data = _factory([_order("A", 25)])
    products = {p.product_id: p for p in data.products}
    assert production_hours(data.orders[0], products) == pytest.approx(2.5)


# ---------- 2. sequencing rules ----------

def test_edd_sorts_by_due_date_then_order_id():
    orders = [_order("C", 1, FRI), _order("B", 1, MON), _order("A", 1, FRI)]
    assert [o.order_id for o in edd_sequence(orders)] == ["B", "A", "C"]


def test_baseline_keeps_arrival_order():
    orders = [_order("C", 1, FRI), _order("B", 1, MON), _order("A", 1, FRI)]
    assert [o.order_id for o in baseline_sequence(orders)] == ["C", "B", "A"]


# ---------- 3. plan_orders: materials, time, deadlines ----------

def test_single_order_on_time():
    data = _factory([_order("A", 20, MON)])
    plan = plan_orders(data, data.orders)
    [line] = plan.orders
    assert line.status == OrderStatus.ON_TIME
    assert (line.start_hour, line.end_hour) == (0, pytest.approx(2.0))
    assert line.hours_available_by_due == 8
    assert line.materials_used == {"M": pytest.approx(20.0)}
    assert line.material_cost_rm == pytest.approx(40.0)
    assert plan.remaining_stock["M"] == pytest.approx(80.0)
    assert plan.hours_used == pytest.approx(2.0)


def test_orders_run_back_to_back():
    data = _factory([_order("A", 20), _order("B", 30)])
    plan = plan_orders(data, data.orders)
    a, b = plan.orders
    assert (a.start_hour, a.end_hour) == (0, pytest.approx(2.0))
    assert (b.start_hour, b.end_hour) == (pytest.approx(2.0), pytest.approx(5.0))


def test_insufficient_material_is_infeasible_and_consumes_nothing():
    data = _factory([_order("A", 150)])
    plan = plan_orders(data, data.orders)
    [line] = plan.orders
    assert line.status == OrderStatus.INFEASIBLE
    assert line.missing_materials == {"M": pytest.approx(50.0)}
    assert "M" in line.reason  # human-readable explanation names the material
    assert line.start_hour is None and line.end_hour is None
    assert line.material_cost_rm == 0
    assert plan.remaining_stock["M"] == pytest.approx(100.0)
    assert plan.hours_used == 0


def test_stock_is_not_double_counted():
    data = _factory([_order("A", 60), _order("B", 60)])
    plan = plan_orders(data, data.orders)
    a, b = plan.orders
    assert a.status == OrderStatus.ON_TIME
    assert b.status == OrderStatus.INFEASIBLE
    assert b.missing_materials == {"M": pytest.approx(20.0)}
    assert plan.remaining_stock["M"] == pytest.approx(40.0)


def test_order_finishing_after_deadline_is_late_not_on_time():
    data = _factory([_order("A", 100, MON)])  # 10 h of work, only 8 h before Monday's deadline
    [line] = plan_orders(data, data.orders).orders
    assert line.status == OrderStatus.LATE
    assert line.end_hour == pytest.approx(10.0)
    assert "late" in line.reason.lower()


def test_infeasible_order_does_not_delay_later_orders():
    data = _factory([_order("BIG", 500), _order("A", 20)])
    big, a = plan_orders(data, data.orders).orders
    assert big.status == OrderStatus.INFEASIBLE
    assert a.start_hour == 0


# ---------- 4. baseline vs optimised ----------

def test_edd_plan_beats_baseline_when_urgent_order_arrives_last():
    # A (7 h, due Fri) arrived before B (2 h, due Mon).
    data = _factory([_order("A", 70, FRI), _order("B", 20, MON)])
    baseline = build_baseline_plan(data)
    optimised = build_optimised_plan(data)

    base_status = {o.order_id: o.status for o in baseline.orders}
    opt_status = {o.order_id: o.status for o in optimised.orders}
    assert base_status == {"A": OrderStatus.ON_TIME, "B": OrderStatus.LATE}
    assert opt_status == {"A": OrderStatus.ON_TIME, "B": OrderStatus.ON_TIME}


# ---------- 5. sample data smoke test ----------

def test_sample_data_plan_is_consistent():
    data = load_production_input()
    plan = build_optimised_plan(data)

    # every order appears exactly once
    assert sorted(o.order_id for o in plan.orders) == sorted(o.order_id for o in data.orders)
    # stock never goes negative
    assert all(qty >= 0 for qty in plan.remaining_stock.values())
    # only 25 kg chicken: 40 + 60 curry puffs need 14 + 21 kg -> exactly one curry order must fail
    curry = [o for o in plan.orders if o.product_id == "CURRY_PUFF"]
    assert sorted(o.status for o in curry) == sorted([OrderStatus.ON_TIME, OrderStatus.INFEASIBLE])
    # nothing infeasible is given a time slot
    for line in plan.orders:
        if line.status == OrderStatus.INFEASIBLE:
            assert line.start_hour is None
