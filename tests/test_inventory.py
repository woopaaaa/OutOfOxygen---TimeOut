"""Module 3 tests. See specs/03-inventory.md."""

from datetime import date

import pytest

from core.inventory import (
    InventoryLedger,
    build_recipe_index,
    material_cost,
    material_report,
    requirements_for,
    total_requirements,
)
from core.loader import load_production_input
from core.models import Order


@pytest.fixture
def data():
    return load_production_input()


@pytest.fixture
def recipe_index(data):
    return build_recipe_index(data.recipes)


@pytest.fixture
def materials(data):
    return {m.material_id: m for m in data.materials}


def _order(oid: str, product: str, qty: int) -> Order:
    return Order(order_id=oid, customer="X", product_id=product, quantity=qty, due_date=date(2026, 10, 30))


# ---------- Part A: calculations ----------

def test_recipe_index_shape(recipe_index):
    assert set(recipe_index) == {"COOKIE_BTR", "KUIH_KELAPA", "CURRY_PUFF"}
    assert recipe_index["COOKIE_BTR"] == {"FLOUR": 0.40, "SUGAR": 0.15, "BUTTER": 0.12, "EGG": 2, "PACK": 1}


def test_requirements_for_one_order(recipe_index):
    assert requirements_for("COOKIE_BTR", 60, recipe_index) == {
        "FLOUR": 24.0, "SUGAR": 9.0, "BUTTER": 7.2, "EGG": 120.0, "PACK": 60.0,
    }


def test_requirements_are_rounded(recipe_index):
    # 0.15 * 3 = 0.44999999999999996 in raw floating point
    assert requirements_for("COOKIE_BTR", 3, recipe_index)["SUGAR"] == 0.45


def test_requirements_for_unknown_product_raises(recipe_index):
    with pytest.raises(KeyError):
        requirements_for("GHOST", 1, recipe_index)


def test_total_requirements_adds_up_orders(recipe_index):
    totals = total_requirements([_order("A", "COOKIE_BTR", 10), _order("B", "KUIH_KELAPA", 10)], recipe_index)
    assert totals["FLOUR"] == pytest.approx(4.0 + 3.0)
    assert totals["EGG"] == pytest.approx(20 + 10)
    assert totals["COCONUT"] == pytest.approx(1.0)
    assert "CHICKEN" not in totals  # nobody ordered curry puffs


def test_material_cost_matches_worked_example(recipe_index, materials):
    needs = requirements_for("COOKIE_BTR", 60, recipe_index)
    assert material_cost(needs, materials) == 394.05


def test_report_shortage_and_purchase(materials):
    [line] = material_report({"BUTTER": 20.0}, materials)
    assert line == {
        "material_id": "BUTTER",
        "name": "Butter",
        "unit": "kg",
        "required": 20.0,
        "in_stock": 15.0,
        "shortage": 5.0,
        "purchase_quantity": 10.0,
        "unit_cost_rm": 28.0,
        "purchase_cost_rm": 280.0,
        "lead_time_days": 4,
    }


def test_report_enough_stock_means_zero_purchase(materials):
    # Flour: stock 120, min 20 -> using 100 leaves exactly the minimum
    [line] = material_report({"FLOUR": 100.0}, materials)
    assert line["shortage"] == 0
    assert line["purchase_quantity"] == 0
    assert line["purchase_cost_rm"] == 0


def test_report_dipping_into_safety_stock(materials):
    # Using 110 flour is possible (no shortage) but leaves less than the minimum of 20
    [line] = material_report({"FLOUR": 110.0}, materials)
    assert line["shortage"] == 0
    assert line["purchase_quantity"] == 10.0


def test_report_sorted_and_one_line_per_material(materials):
    report = material_report({"SUGAR": 1.0, "BUTTER": 1.0, "EGG": 1.0}, materials)
    assert [line["material_id"] for line in report] == ["BUTTER", "EGG", "SUGAR"]


# ---------- Part B: InventoryLedger ----------

def test_ledger_starts_with_stock(data):
    ledger = InventoryLedger(data.materials)
    assert ledger.available("BUTTER") == 15
    assert ledger.available("FLOUR") == 120


def test_ledger_never_double_counts(data):
    ledger = InventoryLedger(data.materials)
    assert ledger.allocate({"BUTTER": 10.0}) is True
    assert ledger.available("BUTTER") == pytest.approx(5.0)
    assert ledger.allocate({"BUTTER": 10.0}) is False
    assert ledger.available("BUTTER") == pytest.approx(5.0)


def test_ledger_is_all_or_nothing(data):
    ledger = InventoryLedger(data.materials)
    before = ledger.snapshot()
    needs = {"FLOUR": 3.0, "CHICKEN": 999.0}
    assert ledger.missing_for(needs) == {"CHICKEN": pytest.approx(974.0)}
    assert ledger.allocate(needs) is False
    assert ledger.snapshot() == before


def test_missing_for_empty_when_enough(data):
    assert InventoryLedger(data.materials).missing_for({"FLOUR": 120.0}) == {}


def test_snapshot_is_a_copy(data):
    ledger = InventoryLedger(data.materials)
    copy = ledger.snapshot()
    copy["FLOUR"] = 0
    assert ledger.available("FLOUR") == 120
