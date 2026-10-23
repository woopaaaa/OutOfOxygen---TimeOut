"""Module 6 tests. See specs/06-api.md."""

import pytest
from fastapi.testclient import TestClient

from core.api import app, build_response
from core.loader import load_production_input

client = TestClient(app)

TOP_LEVEL_KEYS = {
    "generated_at", "planning_start", "schedule", "material_requirements",
    "purchase_request", "metrics", "warnings", "assumptions",
}


def small_payload() -> dict:
    """One product, one material, one order that easily fits."""
    return {
        "materials": [{"material_id": "M", "name": "Mat", "unit": "kg", "quantity_in_stock": 100, "unit_cost_rm": 2.0}],
        "products": [{"product_id": "P", "name": "Prod", "unit": "box", "units_per_hour": 10}],
        "recipes": [{"product_id": "P", "material_id": "M", "quantity_per_unit": 1}],
        "orders": [{"order_id": "A", "customer": "Shop", "product_id": "P", "quantity": 20, "due_date": "2026-10-23"}],
        "capacity": {"planning_start": "2026-10-19", "hours_per_day": 8, "working_days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
    }


# ---------- Part A: build_response ----------

@pytest.fixture
def response():
    return build_response(load_production_input())


def test_response_has_all_contract_keys(response):
    assert set(response) == TOP_LEVEL_KEYS
    assert isinstance(response["generated_at"], str)
    assert response["metrics"] is None  # filled in by module 5 later


def test_schedule_is_the_optimised_plan(response):
    ids = [line["order_id"] for line in response["schedule"]]
    assert ids[:2] == ["ORD-002", "ORD-001"]  # earliest due date first
    assert len(ids) == 6


def test_material_requirements_cover_all_orders(response):
    by_id = {line["material_id"]: line for line in response["material_requirements"]}
    assert by_id["BUTTER"]["required"] == pytest.approx(19.2)  # (60 + 100) boxes x 0.12 kg
    assert by_id["CHICKEN"]["shortage"] == pytest.approx(10.0)  # need 35, have 25


def test_purchase_request(response):
    request = response["purchase_request"]
    assert request["status"] == "pending_approval"
    assert request["requires_role"] == "owner"
    lines = {line["material_id"]: line for line in request["lines"]}
    assert lines["BUTTER"] == {
        "material_id": "BUTTER", "name": "Butter", "unit": "kg",
        "quantity": pytest.approx(9.2), "unit_cost_rm": 28.0, "cost_rm": pytest.approx(257.6),
    }
    assert all(line["quantity"] > 0 for line in request["lines"])
    assert request["total_cost_rm"] == pytest.approx(round(sum(line["cost_rm"] for line in request["lines"]), 2))


def test_warnings_name_every_infeasible_order(response):
    infeasible = [line["order_id"] for line in response["schedule"] if line["status"] == "infeasible"]
    assert infeasible  # the sample data has some
    for order_id in infeasible:
        assert any(order_id in warning for warning in response["warnings"])


def test_assumptions_listed(response):
    assert len(response["assumptions"]) >= 1


# ---------- Part B: the web app ----------

def test_health():
    reply = client.get("/health")
    assert reply.status_code == 200
    assert reply.json() == {"status": "ok"}


def test_sample_plan_over_http():
    reply = client.get("/plan/sample")
    assert reply.status_code == 200
    body = reply.json()
    assert set(body) == TOP_LEVEL_KEYS
    assert body["planning_start"] == "2026-10-21"  # dates become text in JSON
    assert body["schedule"][0]["due_date"] == "2026-10-22"


def test_post_plan_with_own_data():
    reply = client.post("/plan", json=small_payload())
    assert reply.status_code == 200
    [line] = reply.json()["schedule"]
    assert line["status"] == "on_time"
    assert line["end_hour"] == pytest.approx(2.0)


def test_post_invalid_data_returns_422():
    payload = small_payload()
    payload["orders"][0]["product_id"] = "MYSTERY"
    reply = client.post("/plan", json=payload)
    assert reply.status_code == 422
    assert "unknown product 'MYSTERY'" in reply.text


def test_cors_allows_the_frontend():
    reply = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert reply.headers.get("access-control-allow-origin") in ("*", "http://localhost:3000")
