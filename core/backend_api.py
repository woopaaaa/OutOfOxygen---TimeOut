"""Module 13: backend routes (upload data, run plans, approve purchases, export files).

Kept in its own file and plugged into core/api.py with two lines, so it does not
clash with the engine routes. Start the server with:  uvicorn core.api:app --reload

Roles: send the HTTP header  X-Role: owner  or  X-Role: staff  (default: staff).
Only the owner can approve or reject a purchase order.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Response, UploadFile
from pydantic import ValidationError

from core import exporter, store
from core.importer import read_upload
from core.models import ProductionInput

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent / "data"
TEMPLATE_FILES = {"materials.csv", "products.csv", "recipes.csv", "orders.csv", "capacity.json"}
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ---------- helpers ----------

def get_role(x_role: str = Header("staff")) -> str:
    role = x_role.strip().lower()
    if role not in {"owner", "staff"}:
        raise HTTPException(403, "X-Role must be 'owner' or 'staff'")
    return role


def require_owner(role: str = Depends(get_role)) -> str:
    if role != "owner":
        raise HTTPException(403, "Only the owner can do this")
    return role


def problems(exc: ValidationError) -> list[str]:
    """Turn Pydantic's error list into short readable sentences."""
    out = []
    for e in exc.errors():
        where = ".".join(str(p) for p in e["loc"] if p != "__root__")
        message = e["msg"].removeprefix("Value error, ")
        out.append(f"{where}: {message}" if where else message)
    return out


def current_plan():
    from core.api import build_response  # imported here to avoid a circular import

    data, source = store.load_dataset()
    return build_response(data), source


def download(content: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------- data in ----------

@router.get("/data", tags=["data"])
def get_data():
    data, source = store.load_dataset()
    return {"source": source, "data": data}


@router.post("/data/upload", tags=["data"])
async def upload_data(files: list[UploadFile], role: str = Depends(get_role)):
    """Upload the 5 sample-format files, or ONE .xlsx workbook with sheets materials/products/recipes/orders/capacity."""
    contents = [(f.filename or "", await f.read()) for f in files]
    try:
        data = read_upload(contents)
    except ValidationError as exc:
        raise HTTPException(422, {"errors": problems(exc)})
    except FileNotFoundError as exc:
        name = Path(exc.filename).name if exc.filename else str(exc)
        raise HTTPException(400, f"Missing file: {name}")
    except Exception as exc:  # unreadable Excel file, no files, and so on
        raise HTTPException(400, f"Could not read the upload: {exc}")
    store.save_dataset(data)
    store.log_action(role, "data_uploaded", f"{len(data.orders)} orders, {len(data.materials)} materials")
    return {"source": "uploaded", "orders": len(data.orders), "materials": len(data.materials),
            "products": len(data.products), "recipes": len(data.recipes)}


@router.put("/data", tags=["data"])
def put_data(data: ProductionInput, role: str = Depends(get_role)):
    """Save data sent as JSON (invalid data is rejected with 422 automatically)."""
    store.save_dataset(data)
    store.log_action(role, "data_saved", f"{len(data.orders)} orders via JSON")
    return {"source": "uploaded", "orders": len(data.orders)}


@router.post("/data/reset", tags=["data"])
def reset_data(role: str = Depends(get_role)):
    store.reset_dataset()
    store.log_action(role, "data_reset", "back to sample data")
    return {"source": "sample"}


# ---------- plans and approval ----------

@router.get("/plan/current", tags=["plan"])
def plan_current():
    """Plan for the current data. Nothing is saved."""
    plan, source = current_plan()
    return {"source": source, "plan": plan}


@router.post("/plan/run", tags=["plan"])
def plan_run(role: str = Depends(get_role)):
    """The 'Plan production' button: plan + save the purchase request as pending_approval."""
    plan, source = current_plan()
    request = plan["purchase_request"]
    order_id = store.create_purchase_order(request) if request["lines"] else None
    store.log_action(role, "plan_run", f"purchase_order_id={order_id}, total RM {request['total_cost_rm']}")
    return {"source": source, "purchase_order_id": order_id, "plan": plan}


@router.get("/purchase-orders", tags=["approval"])
def purchase_orders():
    return store.list_purchase_orders()


def _decide(order_id: int, status: str, role: str):
    try:
        order = store.decide_purchase_order(order_id, status, role)
    except KeyError:
        raise HTTPException(404, f"Purchase order {order_id} not found")
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    store.log_action(role, f"purchase_{status}", f"purchase_order_id={order_id}")
    return order


@router.post("/purchase-orders/{order_id}/approve", tags=["approval"])
def approve(order_id: int, role: str = Depends(require_owner)):
    return _decide(order_id, "approved", role)


@router.post("/purchase-orders/{order_id}/reject", tags=["approval"])
def reject(order_id: int, role: str = Depends(require_owner)):
    return _decide(order_id, "rejected", role)


@router.get("/activity-log", tags=["approval"])
def activity_log(limit: int = 100):
    return store.list_log(limit)


# ---------- data out ----------

@router.get("/export/schedule.csv", tags=["export"])
def export_schedule():
    plan, _ = current_plan()
    return download(exporter.rows_to_csv(exporter.schedule_rows(plan), exporter.SCHEDULE_COLUMNS),
                    "schedule.csv", "text/csv")


@router.get("/export/materials.csv", tags=["export"])
def export_materials():
    plan, _ = current_plan()
    return download(exporter.rows_to_csv(exporter.material_rows(plan), exporter.MATERIAL_COLUMNS),
                    "materials_report.csv", "text/csv")


@router.get("/export/purchase-request.csv", tags=["export"])
def export_purchase_request():
    plan, _ = current_plan()
    return download(exporter.rows_to_csv(exporter.purchase_rows(plan["purchase_request"]), exporter.PURCHASE_COLUMNS),
                    "purchase_request.csv", "text/csv")


@router.get("/export/plan.xlsx", tags=["export"])
def export_plan_workbook():
    plan, _ = current_plan()
    return download(exporter.plan_workbook(plan), "production_plan.xlsx", XLSX)


@router.get("/export/data.xlsx", tags=["export"])
def export_data_workbook():
    data, _ = store.load_dataset()
    return download(exporter.data_workbook(data), "timed_data.xlsx", XLSX)


# ---------- templates (so users know the exact format) ----------

@router.get("/templates/workbook.xlsx", tags=["templates"])
def template_workbook():
    data, _ = store.load_dataset()
    return download(exporter.data_workbook(data), "timed_template.xlsx", XLSX)


@router.get("/templates/{filename}", tags=["templates"])
def template_file(filename: str):
    if filename not in TEMPLATE_FILES:
        raise HTTPException(404, f"Templates available: {', '.join(sorted(TEMPLATE_FILES))}, workbook.xlsx")
    media = "application/json" if filename.endswith(".json") else "text/csv"
    return download((DATA_DIR / filename).read_bytes(), filename, media)