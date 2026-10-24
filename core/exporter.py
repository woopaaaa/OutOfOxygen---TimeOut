"""Module 12: turn plans and data into downloadable CSV / Excel files.

All functions return the file as bytes, so they can be tested without a server.
"""

import csv
import io

import pandas as pd
from fastapi.encoders import jsonable_encoder

from core.models import ProductionInput

SCHEDULE_COLUMNS = [
    "order_id", "customer", "product_id", "quantity", "due_date", "status",
    "start_hour", "end_hour", "material_cost_rm", "missing_materials", "reason",
]
MATERIAL_COLUMNS = [
    "material_id", "name", "unit", "required", "in_stock", "shortage",
    "purchase_quantity", "unit_cost_rm", "purchase_cost_rm", "lead_time_days",
]
PURCHASE_COLUMNS = ["material_id", "name", "unit", "quantity", "unit_cost_rm", "cost_rm"]


def schedule_rows(plan: dict) -> list[dict]:
    rows = []
    for line in jsonable_encoder(plan["schedule"]):
        row = {c: line.get(c) for c in SCHEDULE_COLUMNS}
        missing = line.get("missing_materials") or {}
        row["missing_materials"] = "; ".join(f"{m}: {amount}" for m, amount in missing.items())
        rows.append(row)
    return rows


def material_rows(plan: dict) -> list[dict]:
    return [{c: r.get(c) for c in MATERIAL_COLUMNS} for r in jsonable_encoder(plan["material_requirements"])]


def purchase_rows(request: dict) -> list[dict]:
    return [{c: r.get(c) for c in PURCHASE_COLUMNS} for r in jsonable_encoder(request["lines"])]


def rows_to_csv(rows: list[dict], columns: list[str]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow({c: ("" if row.get(c) is None else row.get(c)) for c in columns})
    return buffer.getvalue().encode("utf-8-sig")  # utf-8-sig so Excel opens it correctly


def _frame(rows: list[dict], columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=columns)


def _workbook(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            for column in sheet.columns:  # make the columns wide enough to read
                longest = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column)
                sheet.column_dimensions[column[0].column_letter].width = min(max(longest + 2, 10), 60)
    return buffer.getvalue()


def plan_workbook(plan: dict) -> bytes:
    plan = jsonable_encoder(plan)
    metrics = plan.get("metrics") or {}
    metric_rows = [
        {"metric": key, "baseline": metrics.get("baseline", {}).get(key), "optimised": metrics.get("optimised", {}).get(key)}
        for key in metrics.get("optimised", {})
    ]
    request = plan["purchase_request"]
    return _workbook({
        "schedule": _frame(schedule_rows(plan), SCHEDULE_COLUMNS),
        "materials": _frame(material_rows(plan), MATERIAL_COLUMNS),
        "purchase_request": _frame(purchase_rows(request), PURCHASE_COLUMNS),
        "metrics": _frame(metric_rows, ["metric", "baseline", "optimised"]),
        "warnings": pd.DataFrame({"warning": plan["warnings"]}),
    })


def data_workbook(data: ProductionInput) -> bytes:
    """The input data as one workbook. The same layout can be uploaded again (round trip)."""
    d = jsonable_encoder(data)
    capacity = dict(d["capacity"])
    capacity["working_days"] = ",".join(capacity["working_days"])
    return _workbook({
        "materials": pd.DataFrame(d["materials"]),
        "products": pd.DataFrame(d["products"]),
        "recipes": pd.DataFrame(d["recipes"]),
        "orders": pd.DataFrame(d["orders"]),
        "capacity": pd.DataFrame([capacity]),
    })