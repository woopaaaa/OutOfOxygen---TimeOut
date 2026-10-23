"""Module 5 tests. See specs/05-metrics.md."""

from datetime import date

import pytest

from core.loader import load_production_input
from core.metrics import compare_plans, plan_metrics
from core.models import Order, ProductionInput
from core.planner import build_baseline_plan, build_optimised_plan

MON = date(2026, 10, 19)
FRI = date(2026, 10, 23)

KEYS = {
    "orders_total", "orders_on_time", "orders_late", "orders_infeasible", "on_time_rate",
    "total_material_cost_rm", "hours_used", "hours_available", "utilisation",
}


def _order(oid: str, qty: int, due: date) -> Order:
    return Order(order_id=oid, customer="Test", product_id="P", quantity=qty, due_date=due)


def _factory(orders: list[Order]) -> ProductionInput:
    return ProductionInput(
        materials=[{"material_id": "M", "name": "Mat", "unit": "kg", "quantity_in_stock": 100, "unit_cost_rm": 2.0}],
        products=[{"product_id": "P", "name": "Prod", "unit": "box", "units_per_hour": 10}],
        recipes=[{"product_id": "P", "material_id": "M", "quantity_per_unit": 1}],
        orders=orders,
        capacity={"planning_start": MON, "hours_per_day": 8, "working_days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
    )


@pytest.fixture
def ab_data():
    return _factory([_order("A", 70, FRI), _order("B", 20, MON)])


# ---------- Part A: plan_metrics ----------

def test_baseline_metrics_match_worked_example(ab_data):
    metrics = plan_metrics(build_baseline_plan(ab_data), ab_data)
    assert set(metrics) == KEYS
    assert metrics["orders_total"] == 2
    assert metrics["orders_on_time"] == 1
    assert metrics["orders_late"] == 1
    assert metrics["orders_infeasible"] == 0
    assert metrics["on_time_rate"] == 0.5
    assert metrics["total_material_cost_rm"] == pytest.approx(180.0)
    assert metrics["hours_used"] == pytest.approx(9.0)
    assert metrics["hours_available"] == 40
    assert metrics["utilisation"] == pytest.approx(0.225, abs=0.006)


def test_optimised_metrics_match_worked_example(ab_data):
    metrics = plan_metrics(build_optimised_plan(ab_data), ab_data)
    assert metrics["orders_on_time"] == 2
    assert metrics["orders_late"] == 0
    assert metrics["on_time_rate"] == 1.0


def test_infeasible_orders_cost_nothing():
    data = _factory([_order("BIG", 150, FRI)])  # needs 150 kg, only 100 in stock
    metrics = plan_metrics(build_optimised_plan(data), data)
    assert metrics["orders_infeasible"] == 1
    assert metrics["on_time_rate"] == 0
    assert metrics["total_material_cost_rm"] == 0
    assert metrics["hours_used"] == 0
    assert metrics["utilisation"] == 0


def test_rate_is_rounded():
    # 3 orders, 1 on time -> 0.333... -> 0.33
    data = _factory([_order("A", 10, MON), _order("B", 1000, FRI), _order("C", 1000, FRI)])
    metrics = plan_metrics(build_optimised_plan(data), data)
    assert metrics["orders_total"] == 3
    assert metrics["on_time_rate"] == 0.33


# ---------- Part B: compare_plans ----------

def test_compare_plans_shape(ab_data):
    result = compare_plans(ab_data)
    assert set(result) == {"baseline", "optimised"}
    assert result["baseline"]["on_time_rate"] == 0.5
    assert result["optimised"]["on_time_rate"] == 1.0


def test_compare_plans_on_sample_data_is_consistent():
    result = compare_plans(load_production_input())
    for metrics in result.values():
        assert set(metrics) == KEYS
        assert metrics["orders_total"] == 6
        assert metrics["orders_on_time"] + metrics["orders_late"] + metrics["orders_infeasible"] == 6
        assert 0 <= metrics["utilisation"] <= 1


def test_sample_data_shows_a_real_improvement():
    # The demo data must show the benefit honestly: same orders and stock, better plan.
    result = compare_plans(load_production_input())
    assert result["optimised"]["orders_on_time"] > result["baseline"]["orders_on_time"]
