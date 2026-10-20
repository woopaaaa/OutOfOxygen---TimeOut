from datetime import date

import pytest
from pydantic import ValidationError

from timed.inventory import (
    InventoryLedger,
    build_recipe_index,
    material_cost,
    requirements_for,
    shortage_report,
    total_requirements,
)
from timed.loader import load_production_input
from timed.models import Order, ProductionInput


@pytest.fixture
def data() -> ProductionInput:
    return load_production_input()


@pytest.fixture
def recipe_index(data):
    return build_recipe_index(data.recipes)


@pytest.fixture
def materials(data):
    return {m.material_id: m for m in data.materials}


def _order(oid: str, product: str, qty: int) -> Order:
    return Order(order_id=oid, customer="X", product_id=product, quantity=qty, due_date=date(2026, 10, 30))


def test_sample_data_loads(data):
    assert len(data.products) >= 3 and len(data.materials) >= 5 and len(data.orders) >= 5
    assert data.materials[0].lead_time_days is not None


def test_requirements_for_single_order(recipe_index):
    assert requirements_for("COOKIE_BTR", 60, recipe_index) == {
        "FLOUR": 24.0, "SUGAR": 9.0, "BUTTER": 7.2, "EGG": 120.0, "PACK": 60.0,
    }


def test_total_requirements_aggregates_orders(recipe_index):
    orders = [_order("A", "COOKIE_BTR", 10), _order("B", "KUIH_KELAPA", 10)]
    totals = total_requirements(orders, recipe_index)
    assert totals["FLOUR"] == pytest.approx(4.0 + 3.0)
    assert totals["EGG"] == pytest.approx(20 + 10)
    assert totals["COCONUT"] == pytest.approx(1.0)


def test_material_cost(recipe_index, materials):
    needs = requirements_for("COOKIE_BTR", 60, recipe_index)
    # 24*3.20 + 9*2.85 + 7.2*28 + 120*0.45 + 60*0.60
    assert material_cost(needs, materials) == pytest.approx(394.05)


def test_shortage_and_purchase_includes_min_stock(materials):
    # Butter: stock 15, min 5, need 20 -> short 5 for production, buy 10 to restore safety stock.
    [line] = shortage_report({"BUTTER": 20.0}, materials)
    assert line.production_shortage == pytest.approx(5.0)
    assert line.purchase_quantity == pytest.approx(10.0)
    assert line.purchase_cost_rm == pytest.approx(280.0)
    assert line.lead_time_days == 4


def test_no_shortage_when_stock_sufficient(materials):
    # Flour: stock 120, min 20 -> 100 usable without dipping below min.
    assert shortage_report({"FLOUR": 100.0}, materials) == []


def test_stock_dipping_into_safety_triggers_purchase_but_not_production_shortage(materials):
    [line] = shortage_report({"FLOUR": 110.0}, materials)
    assert line.production_shortage == 0
    assert line.purchase_quantity == pytest.approx(10.0)


def test_ledger_never_double_counts(data):
    ledger = InventoryLedger(data.materials)
    assert ledger.allocate({"BUTTER": 10.0})
    assert ledger.available("BUTTER") == pytest.approx(5.0)
    # Second order wants 10 again: must fail, not go negative.
    assert not ledger.allocate({"BUTTER": 10.0})
    assert ledger.available("BUTTER") == pytest.approx(5.0)


def test_ledger_allocation_is_all_or_nothing(data):
    ledger = InventoryLedger(data.materials)
    before = ledger.snapshot()
    needs = {"FLOUR": 10.0, "CHICKEN": 999.0}
    assert ledger.missing_for(needs) == {"CHICKEN": pytest.approx(974.0)}
    assert not ledger.allocate(needs)
    assert ledger.snapshot() == before


def test_unknown_product_in_order_is_rejected(data):
    payload = data.model_dump()
    payload["orders"][0]["product_id"] = "MYSTERY"
    with pytest.raises(ValidationError, match="unknown product 'MYSTERY'"):
        ProductionInput(**payload)


def test_product_without_recipe_reported_as_missing_information(data):
    payload = data.model_dump()
    payload["recipes"] = [r for r in payload["recipes"] if r["product_id"] != "CURRY_PUFF"]
    with pytest.raises(ValidationError, match="has no recipe"):
        ProductionInput(**payload)


def test_negative_stock_rejected(data):
    payload = data.model_dump()
    payload["materials"][0]["quantity_in_stock"] = -1
    with pytest.raises(ValidationError):
        ProductionInput(**payload)
