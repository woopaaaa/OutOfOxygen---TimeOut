"""Module 4 tests. See specs/04-planner.md.

Most tests use a tiny factory so every number can be checked by hand:
  * product P, made at 10 units/hour, needs 1 kg of material M per unit
  * material M: 100 kg in stock, RM 2.00/kg (name "Mat")
  * planning starts Monday 2026-10-19, 8 h/day, Mon-Fri
"""

from datetime import date

import pytest

from core.loader import load_production_input
from core.models import Order, ProductionInput
from core.planner import (
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


# ---------- 1. time helpers ----------

@pytest.mark.parametrize(
    ("due", "expected_hours"),
    [
        (date(2026, 10, 19), 8),   # due on the start day: that whole day counts
        (date(2026, 10, 23), 40),  # Mon..Fri
        (date(2026, 10, 25), 40),  # the weekend adds nothing
        (date(2026, 10, 26), 48),  # next Monday
        (date(2026, 10, 18), 0),   # due before planning starts
    ],
)
def test_working_hours_until(due, expected_hours):
    capacity = _factory([_order("A", 1)]).capacity
    assert working_hours_until(capacity, due) == expected_hours


def test_working_hours_until_sample_data():
    capacity = load_production_input().capacity  # starts Wed 21 Oct, Mon-Sat
    assert working_hours_until(capacity, date(2026, 10, 22)) == 16
    assert working_hours_until(capacity, date(2026, 10, 26)) == 40


def test_production_hours():
    data = _factory([_order("A", 25)])
    products = {p.product_id: p for p in data.products}
    assert production_hours(data.orders[0], products) == pytest.approx(2.5)


# ---------- 2. sequences ----------

def test_edd_sorts_by_due_date_then_order_id():
    orders = [_order("C", 1, FRI), _order("B", 1, MON), _order("A", 1, FRI)]
    assert [o.order_id for o in edd_sequence(orders)] == ["B", "A", "C"]


def test_baseline_keeps_arrival_order():
    orders = [_order("C", 1, FRI), _order("B", 1, MON), _order("A", 1, FRI)]
    assert [o.order_id for o in baseline_sequence(orders)] == ["C", "B", "A"]


def test_sequences_do_not_change_the_input_list():
    orders = [_order("C", 1, FRI), _order("B", 1, MON)]
    edd_sequence(orders)
    baseline_sequence(orders).reverse()
    assert [o.order_id for o in orders] == ["C", "B"]


# ---------- 3. plan_orders ----------

def test_single_order_on_time():
    data = _factory([_order("A", 20, MON)])
    plan = plan_orders(data, data.orders)
    [line] = plan["schedule"]
    assert line["status"] == "on_time"
    assert line["start_hour"] == 0
    assert line["end_hour"] == pytest.approx(2.0)
    assert line["material_cost_rm"] == pytest.approx(40.0)
    assert line["missing_materials"] == {}
    assert line["order_id"] == "A" and line["customer"] == "Test" and line["quantity"] == 20
    assert line["due_date"] == MON
    assert plan["remaining_stock"]["M"] == pytest.approx(80.0)
    assert plan["hours_used"] == pytest.approx(2.0)


def test_orders_run_back_to_back():
    data = _factory([_order("A", 20), _order("B", 30)])
    a, b = plan_orders(data, data.orders)["schedule"]
    assert (a["start_hour"], a["end_hour"]) == (0, pytest.approx(2.0))
    assert (b["start_hour"], b["end_hour"]) == (pytest.approx(2.0), pytest.approx(5.0))


def test_not_enough_material_is_infeasible_and_uses_nothing():
    data = _factory([_order("A", 150)])
    plan = plan_orders(data, data.orders)
    [line] = plan["schedule"]
    assert line["status"] == "infeasible"
    assert line["missing_materials"] == {"M": pytest.approx(50.0)}
    assert "Mat" in line["reason"]  # names the material so the owner understands
    assert line["start_hour"] is None and line["end_hour"] is None
    assert line["material_cost_rm"] == 0
    assert plan["remaining_stock"]["M"] == pytest.approx(100.0)
    assert plan["hours_used"] == 0


def test_stock_is_not_double_counted():
    data = _factory([_order("A", 60), _order("B", 60)])
    plan = plan_orders(data, data.orders)
    a, b = plan["schedule"]
    assert a["status"] == "on_time"
    assert b["status"] == "infeasible"
    assert b["missing_materials"] == {"M": pytest.approx(20.0)}
    assert plan["remaining_stock"]["M"] == pytest.approx(40.0)


def test_finishing_after_deadline_is_late():
    data = _factory([_order("A", 100, MON)])  # 10 h of work, only 8 h before Monday ends
    [line] = plan_orders(data, data.orders)["schedule"]
    assert line["status"] == "late"
    assert line["end_hour"] == pytest.approx(10.0)
    assert "late" in line["reason"].lower()
    assert line["material_cost_rm"] == pytest.approx(200.0)  # late orders are still made


def test_infeasible_order_does_not_move_the_clock():
    data = _factory([_order("BIG", 500), _order("A", 20)])
    big, a = plan_orders(data, data.orders)["schedule"]
    assert big["status"] == "infeasible"
    assert a["start_hour"] == 0


# ---------- 4. baseline vs optimised ----------

def test_optimised_beats_baseline_when_urgent_order_arrives_last():
    data = _factory([_order("A", 70, FRI), _order("B", 20, MON)])
    baseline = {line["order_id"]: line["status"] for line in build_baseline_plan(data)["schedule"]}
    optimised = {line["order_id"]: line["status"] for line in build_optimised_plan(data)["schedule"]}
    assert baseline == {"A": "on_time", "B": "late"}
    assert optimised == {"A": "on_time", "B": "on_time"}


# ---------- 5. sample data ----------

def test_sample_plan_is_consistent():
    data = load_production_input()
    plan = build_optimised_plan(data)
    ids = [line["order_id"] for line in plan["schedule"]]
    assert sorted(ids) == sorted(o.order_id for o in data.orders)  # every order exactly once
    assert all(qty >= 0 for qty in plan["remaining_stock"].values())  # stock never negative
    # only 25 kg chicken, the two curry puff orders need 14 + 21 kg -> exactly one must fail
    curry = sorted(line["status"] for line in plan["schedule"] if line["product_id"] == "CURRY_PUFF")
    assert curry == ["infeasible", "on_time"]
