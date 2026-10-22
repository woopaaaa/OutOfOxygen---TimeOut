"""Module 2 tests. See specs/02-loader.md."""

import shutil
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.loader import load_production_input
from core.models import ProductionInput

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def data_copy(tmp_path: Path) -> Path:
    """A private copy of data/ that a test can edit without touching the real files."""
    copy = tmp_path / "data"
    shutil.copytree(DATA_DIR, copy)
    return copy


# ---------- loading the sample data ----------

def test_loads_sample_data_by_default():
    data = load_production_input()
    assert isinstance(data, ProductionInput)
    assert len(data.materials) == 7
    assert len(data.products) == 3
    assert len(data.recipes) == 14
    assert len(data.orders) == 6


def test_values_have_the_right_types():
    data = load_production_input()
    flour = next(m for m in data.materials if m.material_id == "FLOUR")
    assert flour.quantity_in_stock == 120
    assert flour.unit_cost_rm == pytest.approx(3.20)
    assert flour.lead_time_days == 2
    first_order = next(o for o in data.orders if o.order_id == "ORD-001")
    assert first_order.quantity == 60
    assert first_order.due_date == date(2026, 10, 23)


def test_capacity_loaded_and_note_ignored():
    data = load_production_input()
    assert data.capacity.hours_per_day == 8
    assert data.capacity.planning_start == date(2026, 10, 21)
    assert data.capacity.working_days == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def test_default_folder_does_not_depend_on_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # run from somewhere with no data/ folder
    assert len(load_production_input().orders) == 6


# ---------- custom folder ----------

def test_reads_from_a_given_folder(data_copy):
    orders = data_copy / "orders.csv"
    orders.write_text(
        "order_id,customer,product_id,quantity,due_date\n"
        "X-1,Test Shop,COOKIE_BTR,5,2026-10-30\n",
        encoding="utf-8",
    )
    data = load_production_input(data_copy)
    assert [o.order_id for o in data.orders] == ["X-1"]


def test_empty_lead_time_becomes_none(data_copy):
    materials = data_copy / "materials.csv"
    text = materials.read_text(encoding="utf-8").replace("COCONUT,Grated coconut,kg,10,9.50,2,1", "COCONUT,Grated coconut,kg,10,9.50,2,")
    materials.write_text(text, encoding="utf-8")
    data = load_production_input(data_copy)
    coconut = next(m for m in data.materials if m.material_id == "COCONUT")
    assert coconut.lead_time_days is None


# ---------- problems ----------

@pytest.mark.parametrize("filename", ["materials.csv", "products.csv", "recipes.csv", "orders.csv", "capacity.json"])
def test_missing_file_names_the_file(data_copy, filename):
    (data_copy / filename).unlink()
    with pytest.raises(FileNotFoundError, match=filename.replace(".", r"\.")):
        load_production_input(data_copy)


def test_bad_values_are_rejected_by_the_models(data_copy):
    materials = data_copy / "materials.csv"
    text = materials.read_text(encoding="utf-8").replace("FLOUR,Wheat flour,kg,120", "FLOUR,Wheat flour,kg,-5")
    materials.write_text(text, encoding="utf-8")
    with pytest.raises(ValidationError):
        load_production_input(data_copy)


def test_cross_checks_still_run(data_copy):
    orders = data_copy / "orders.csv"
    orders.write_text(
        "order_id,customer,product_id,quantity,due_date\n"
        "X-1,Test Shop,MYSTERY,5,2026-10-30\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="unknown product 'MYSTERY'"):
        load_production_input(data_copy)
