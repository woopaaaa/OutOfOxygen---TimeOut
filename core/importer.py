"""Module 11: read uploaded files into a ProductionInput.

Two ways to upload:
  1. the five files  materials.csv, products.csv, recipes.csv, orders.csv, capacity.json
  2. ONE Excel workbook (.xlsx) with sheets named
     materials, products, recipes, orders, capacity

Both ways are written to a temporary folder and read by core/loader.py,
so the validation rules are exactly the same as for the sample data.
"""

import io
import json
import tempfile
from pathlib import Path

import pandas as pd

from core.loader import load_production_input
from core.models import ProductionInput

CSV_NAMES = ["materials.csv", "products.csv", "recipes.csv", "orders.csv"]
SHEETS = ["materials", "products", "recipes", "orders", "capacity"]
DATE_COLUMNS = {"orders": ["due_date"], "capacity": ["planning_start"]}


def _clean_cell(value):
    """Excel gives us NaN, floats like 60.0 and Timestamps; turn them into plain text/numbers."""
    if pd.isna(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _sheet_to_frame(book: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    if sheet not in book.sheet_names:
        raise FileNotFoundError(f"Excel sheet '{sheet}' is missing (found: {', '.join(book.sheet_names)})")
    frame = book.parse(sheet)
    frame.columns = [str(c).strip() for c in frame.columns]
    for column in DATE_COLUMNS.get(sheet, []):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column]).dt.strftime("%Y-%m-%d")
    return frame.astype(object).map(_clean_cell)


def _write_workbook(content: bytes, folder: Path) -> None:
    book = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    for sheet in ["materials", "products", "recipes", "orders"]:
        _sheet_to_frame(book, sheet).to_csv(folder / f"{sheet}.csv", index=False)
    capacity = _sheet_to_frame(book, "capacity")
    if len(capacity) < 1:
        raise ValueError("Excel sheet 'capacity' must have one row of data")
    row = capacity.iloc[0].to_dict()
    days = row.get("working_days", "")
    row["working_days"] = [d.strip() for d in str(days).split(",") if d.strip()]
    (folder / "capacity.json").write_text(json.dumps(row, default=str), encoding="utf-8")


def read_upload(files: list[tuple[str, bytes]]) -> ProductionInput:
    """files = [(file name, file bytes), ...]. Raises FileNotFoundError / ValueError / ValidationError."""
    if not files:
        raise ValueError("No files were uploaded")
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        workbooks = [f for f in files if f[0].lower().endswith((".xlsx", ".xlsm"))]
        if workbooks:
            _write_workbook(workbooks[0][1], folder)
        else:
            wanted = set(CSV_NAMES) | {"capacity.json"}
            for name, content in files:
                base = Path(name).name.lower()  # drop any folder part, ignore capital letters
                if base in wanted:
                    (folder / base).write_bytes(content)
        return load_production_input(folder)