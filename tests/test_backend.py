"""Module 10-13 tests: storage, upload, approval, export. See core/backend_api.py."""

import io
import shutil
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from core.api import app
from core.exporter import data_workbook
from core.loader import load_production_input

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OWNER = {"X-Role": "owner"}
STAFF = {"X-Role": "staff"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A client whose database is a throw-away file, so tests never touch timed.db."""
    monkeypatch.setenv("TIMED_DB", str(tmp_path / "test.db"))
    return TestClient(app)


def csv_files(folder: Path = DATA_DIR):
    names = ["materials.csv", "products.csv", "recipes.csv", "orders.csv", "capacity.json"]
    return [("files", (n, (folder / n).read_bytes())) for n in names]


# ---------- data in ----------

def test_starts_with_sample_data(client):
    body = client.get("/data").json()
    assert body["source"] == "sample"
    assert len(body["data"]["orders"]) == 6


def test_upload_five_files(client, tmp_path):
    folder = tmp_path / "mine"
    shutil.copytree(DATA_DIR, folder)
    (folder / "orders.csv").write_text(
        "order_id,customer,product_id,quantity,due_date\nX-1,Test Shop,COOKIE_BTR,5,2026-10-30\n", encoding="utf-8")
    r = client.post("/data/upload", files=csv_files(folder), headers=STAFF)
    assert r.status_code == 200, r.text
    assert r.json()["orders"] == 1
    assert client.get("/data").json()["source"] == "uploaded"


def test_upload_excel_round_trip(client):
    workbook = data_workbook(load_production_input())
    r = client.post("/data/upload", files=[("files", ("data.xlsx", workbook))])
    assert r.status_code == 200, r.text
    assert r.json() == {"source": "uploaded", "orders": 6, "materials": 7, "products": 3, "recipes": 14}
    got = client.get("/data").json()["data"]
    assert got["orders"][0]["due_date"] == "2026-10-27"
    assert got["capacity"]["working_days"] == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def test_upload_bad_value_gives_422_with_readable_errors(client, tmp_path):
    folder = tmp_path / "bad"
    shutil.copytree(DATA_DIR, folder)
    text = (folder / "materials.csv").read_text(encoding="utf-8").replace("FLOUR,Wheat flour,kg,120", "FLOUR,Wheat flour,kg,-5")
    (folder / "materials.csv").write_text(text, encoding="utf-8")
    r = client.post("/data/upload", files=csv_files(folder))
    assert r.status_code == 422
    assert any("quantity_in_stock" in e for e in r.json()["detail"]["errors"])


def test_upload_unknown_product_gives_422(client, tmp_path):
    folder = tmp_path / "bad2"
    shutil.copytree(DATA_DIR, folder)
    (folder / "orders.csv").write_text(
        "order_id,customer,product_id,quantity,due_date\nX-1,Shop,MYSTERY,5,2026-10-30\n", encoding="utf-8")
    r = client.post("/data/upload", files=csv_files(folder))
    assert r.status_code == 422
    assert "unknown product 'MYSTERY'" in " ".join(r.json()["detail"]["errors"])


def test_upload_missing_file_names_it(client):
    files = [f for f in csv_files() if f[1][0] != "orders.csv"]
    r = client.post("/data/upload", files=files)
    assert r.status_code == 400
    assert "orders.csv" in r.json()["detail"]


def test_upload_garbage_excel_is_a_clean_400(client):
    r = client.post("/data/upload", files=[("files", ("x.xlsx", b"not an excel file"))])
    assert r.status_code == 400


def test_reset_goes_back_to_sample(client):
    client.post("/data/upload", files=[("files", ("d.xlsx", data_workbook(load_production_input())))])
    assert client.get("/data").json()["source"] == "uploaded"
    client.post("/data/reset")
    assert client.get("/data").json()["source"] == "sample"


# ---------- plans and approval ----------

def test_plan_current_uses_stored_data(client):
    body = client.get("/plan/current").json()
    assert body["plan"]["metrics"]["optimised"]["orders_total"] == 6


def test_plan_run_creates_pending_purchase_order(client):
    body = client.post("/plan/run", headers=STAFF).json()
    assert body["purchase_order_id"] == 1
    orders = client.get("/purchase-orders").json()
    assert orders[0]["status"] == "pending_approval"
    assert orders[0]["request"]["requires_role"] == "owner"


def test_staff_cannot_approve(client):
    client.post("/plan/run")
    assert client.post("/purchase-orders/1/approve", headers=STAFF).status_code == 403
    assert client.post("/purchase-orders/1/approve").status_code == 403  # no header = staff
    assert client.get("/purchase-orders").json()[0]["status"] == "pending_approval"


def test_owner_approves_once(client):
    client.post("/plan/run")
    r = client.post("/purchase-orders/1/approve", headers=OWNER)
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    assert r.json()["decided_by"] == "owner"
    assert client.post("/purchase-orders/1/approve", headers=OWNER).status_code == 409
    assert client.post("/purchase-orders/1/reject", headers=OWNER).status_code == 409


def test_owner_can_reject_and_missing_order_is_404(client):
    client.post("/plan/run")
    assert client.post("/purchase-orders/1/reject", headers=OWNER).json()["status"] == "rejected"
    assert client.post("/purchase-orders/99/approve", headers=OWNER).status_code == 404


def test_bad_role_is_rejected(client):
    assert client.post("/plan/run", headers={"X-Role": "boss"}).status_code == 403


def test_activity_log_newest_first(client):
    client.post("/plan/run", headers=STAFF)
    client.post("/purchase-orders/1/approve", headers=OWNER)
    log = client.get("/activity-log").json()
    assert [row["action"] for row in log] == ["purchase_approved", "plan_run"]
    assert log[0]["actor_role"] == "owner"


# ---------- data out ----------

def test_export_schedule_csv(client):
    r = client.get("/export/schedule.csv")
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    frame = pd.read_csv(io.BytesIO(r.content))
    assert len(frame) == 6
    assert {"order_id", "status", "reason"} <= set(frame.columns)


def test_export_purchase_request_csv_total_matches_plan(client):
    frame = pd.read_csv(io.BytesIO(client.get("/export/purchase-request.csv").content))
    plan = client.get("/plan/current").json()["plan"]
    assert round(frame["cost_rm"].sum(), 2) == plan["purchase_request"]["total_cost_rm"]


def test_export_materials_csv(client):
    frame = pd.read_csv(io.BytesIO(client.get("/export/materials.csv").content))
    assert "BUTTER" in set(frame["material_id"])


def test_export_plan_workbook_has_all_sheets(client):
    r = client.get("/export/plan.xlsx")
    sheets = pd.read_excel(io.BytesIO(r.content), sheet_name=None)
    assert set(sheets) == {"schedule", "materials", "purchase_request", "metrics", "warnings"}
    assert len(sheets["schedule"]) == 6


def test_export_data_workbook_can_be_uploaded_again(client):
    workbook = client.get("/export/data.xlsx").content
    r = client.post("/data/upload", files=[("files", ("again.xlsx", workbook))])
    assert r.status_code == 200
    assert r.json()["orders"] == 6


# ---------- templates ----------

def test_templates(client):
    assert client.get("/templates/orders.csv").status_code == 200
    assert client.get("/templates/capacity.json").json()["hours_per_day"] == 8
    assert client.get("/templates/workbook.xlsx").status_code == 200
    assert client.get("/templates/secrets.txt").status_code == 404