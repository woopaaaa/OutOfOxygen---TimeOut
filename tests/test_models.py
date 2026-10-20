"""Module 1 tests — see specs/01-models.md."""

from datetime import date

import pytest
from pydantic import ValidationError

from timed.models import Capacity, Material, Order, Product, ProductionInput, RecipeLine


def valid_payload() -> dict:
    """Smallest valid input: 1 material, 1 product, 1 recipe line, 1 order."""
    return {
        "materials": [{"material_id": "FLOUR", "name": "Flour", "unit": "kg", "quantity_in_stock": 10, "unit_cost_rm": 3.2}],
        "products": [{"product_id": "COOKIE", "name": "Cookie", "unit": "box", "units_per_hour": 40}],
        "recipes": [{"product_id": "COOKIE", "material_id": "FLOUR", "quantity_per_unit": 0.4}],
        "orders": [{"order_id": "O1", "customer": "Ah Seng", "product_id": "COOKIE", "quantity": 5, "due_date": "2026-10-23"}],
        "capacity": {"planning_start": "2026-10-21", "hours_per_day": 8, "working_days": ["Mon", "Tue"]},
    }


# ---------- single models ----------

def test_valid_input_parses_and_converts_types():
    data = ProductionInput(**valid_payload())
    assert data.orders[0].due_date == date(2026, 10, 23)  # string -> date
    assert isinstance(data.capacity, Capacity)


def test_material_defaults():
    m = Material(material_id="X", name="X", unit="kg", quantity_in_stock=1, unit_cost_rm=1)
    assert m.min_stock == 0
    assert m.lead_time_days is None


@pytest.mark.parametrize(
    ("model", "kwargs"),
    [
        (Material, dict(material_id="X", name="X", unit="kg", quantity_in_stock=-1, unit_cost_rm=1)),
        (Material, dict(material_id="X", name="X", unit="kg", quantity_in_stock=1, unit_cost_rm=-0.01)),
        (Material, dict(material_id="", name="X", unit="kg", quantity_in_stock=1, unit_cost_rm=1)),
        (Material, dict(material_id="X", name="X", unit="kg", quantity_in_stock=1, unit_cost_rm=1, lead_time_days=-2)),
        (Product, dict(product_id="P", name="P", unit="box", units_per_hour=0)),
        (RecipeLine, dict(product_id="P", material_id="M", quantity_per_unit=0)),
        (Order, dict(order_id="O", customer="C", product_id="P", quantity=0, due_date="2026-10-23")),
        (Order, dict(order_id="O", customer="C", product_id="P", quantity=5, due_date="not-a-date")),
        (Capacity, dict(planning_start="2026-10-21", hours_per_day=25, working_days=["Mon"])),
        (Capacity, dict(planning_start="2026-10-21", hours_per_day=8, working_days=[])),
        (Capacity, dict(planning_start="2026-10-21", hours_per_day=8, working_days=["Funday"])),
    ],
    ids=[
        "negative-stock", "negative-cost", "empty-id", "negative-lead-time", "zero-rate",
        "zero-recipe-qty", "zero-order-qty", "bad-date", "25h-day", "no-working-days", "bad-weekday",
    ],
)
def test_invalid_single_fields_rejected(model, kwargs):
    with pytest.raises(ValidationError):
        model(**kwargs)


def test_empty_orders_rejected():
    payload = valid_payload()
    payload["orders"] = []
    with pytest.raises(ValidationError):
        ProductionInput(**payload)


# ---------- cross-checks ----------

def _expect_error(payload: dict, phrase: str) -> None:
    with pytest.raises(ValidationError, match=phrase):
        ProductionInput(**payload)


def test_duplicate_material_id():
    p = valid_payload()
    p["materials"].append(dict(p["materials"][0]))
    _expect_error(p, "Duplicate material_id")


def test_duplicate_product_id():
    p = valid_payload()
    p["products"].append(dict(p["products"][0]))
    _expect_error(p, "Duplicate product_id")


def test_duplicate_order_id():
    p = valid_payload()
    p["orders"].append(dict(p["orders"][0]))
    _expect_error(p, "Duplicate order_id")


def test_recipe_unknown_material():
    p = valid_payload()
    p["recipes"].append({"product_id": "COOKIE", "material_id": "UNOBTAINIUM", "quantity_per_unit": 1})
    _expect_error(p, "unknown material 'UNOBTAINIUM'")


def test_recipe_unknown_product():
    p = valid_payload()
    p["recipes"].append({"product_id": "GHOST", "material_id": "FLOUR", "quantity_per_unit": 1})
    _expect_error(p, "unknown product 'GHOST'")


def test_duplicate_recipe_line():
    p = valid_payload()
    p["recipes"].append(dict(p["recipes"][0]))
    _expect_error(p, "Duplicate recipe line")


def test_order_unknown_product():
    p = valid_payload()
    p["orders"][0]["product_id"] = "MYSTERY"
    _expect_error(p, "unknown product 'MYSTERY'")


def test_order_for_product_without_recipe():
    p = valid_payload()
    p["products"].append({"product_id": "CAKE", "name": "Cake", "unit": "pc", "units_per_hour": 5})
    p["orders"].append({"order_id": "O2", "customer": "C", "product_id": "CAKE", "quantity": 1, "due_date": "2026-10-23"})
    _expect_error(p, "Missing information.*has no recipe")


def test_all_problems_reported_together():
    p = valid_payload()
    p["materials"].append(dict(p["materials"][0]))             # duplicate material
    p["orders"][0]["product_id"] = "MYSTERY"                    # unknown product
    with pytest.raises(ValidationError) as excinfo:
        ProductionInput(**p)
    message = str(excinfo.value)
    assert "Duplicate material_id" in message and "unknown product 'MYSTERY'" in message
