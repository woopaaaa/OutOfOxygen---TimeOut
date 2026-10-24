"""Module 8 tests. See specs/07-forecasting.md."""

from datetime import date

from core.models import Capacity, Material, Order, Product, ProductionInput, RecipeLine
from core.stockout import predict_stockouts, weekly_demand


def small_input(stock=100, lead=2, orders=None):
    """One product using 1 kg of M per unit; Mon-Fri; plan starts Monday 2026-10-19."""
    return ProductionInput(
        materials=[Material(material_id="M", name="Mat", unit="kg", quantity_in_stock=stock, unit_cost_rm=2.0,
                            min_stock=10, lead_time_days=lead)],
        products=[Product(product_id="P", name="Prod", unit="box", units_per_hour=10)],
        recipes=[RecipeLine(product_id="P", material_id="M", quantity_per_unit=1)],
        orders=orders or [Order(order_id="A", customer="Shop", product_id="P", quantity=5, due_date=date(2026, 10, 23))],
        capacity=Capacity(planning_start=date(2026, 10, 19), hours_per_day=8, working_days=["Mon", "Tue", "Wed", "Thu", "Fri"]),
    )


def forecast(units, upper=None, weeks=(date(2026, 10, 19), date(2026, 10, 26))):
    return [{"week_start": w, "product_id": "P", "forecast_units": units, "lower_80": units, "upper_80": upper or units}
            for w in weeks]


def test_runs_out_on_the_right_day():
    # 50 units/week = 10 kg per working day; 35 kg lasts Mon, Tue, Wed and fails on Thu.
    result = predict_stockouts(small_input(stock=35, lead=1), forecast(50))
    m = result["materials"][0]
    assert m["stockout_date"] == date(2026, 10, 22)
    assert m["days_of_cover"] == 3.5
    assert m["order_by"] == date(2026, 10, 21)
    assert m["status"] == "reorder_now"
    assert m["need_until_horizon"] == 100
    assert m["recommended_order_qty"] == 75  # 100 + min 10 - 35
    assert m["recommended_order_cost_rm"] == 150
    assert result["products_at_risk"][0]["limiting_material"] == "M"


def test_critical_when_lead_time_too_long():
    m = predict_stockouts(small_input(stock=35, lead=7), forecast(50))["materials"][0]
    assert m["status"] == "critical"


def test_ok_and_watch():
    assert predict_stockouts(small_input(stock=500), forecast(50))["materials"][0]["status"] == "ok"
    m = predict_stockouts(small_input(stock=120), forecast(50, upper=80))["materials"][0]
    assert m["stockout_date"] is None
    assert m["stockout_date_high_demand"] is not None
    assert m["status"] == "watch"


def test_confirmed_orders_raise_demand():
    big = [Order(order_id="A", customer="Shop", product_id="P", quantity=200, due_date=date(2026, 10, 23))]
    demand = weekly_demand(forecast(50), big, "expected")
    assert demand[(date(2026, 10, 19), "P")] == 200
    assert demand[(date(2026, 10, 26), "P")] == 50


def test_first_week_is_prorated_from_planning_start():
    data = small_input(stock=1000)
    data.capacity.planning_start = date(2026, 10, 22)  # Thursday: only Thu and Fri left in week 1
    m = predict_stockouts(data, forecast(50))["materials"][0]
    assert m["need_until_horizon"] == 70  # 2 days x 10 + 50


def test_unknown_lead_time_warns():
    result = predict_stockouts(small_input(stock=35, lead=None), forecast(50))
    assert result["warnings"]
