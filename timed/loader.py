"""Load a ProductionInput from CSV/JSON files (the replaceable data layer)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from timed.models import Capacity, Material, Order, Product, ProductionInput, RecipeLine

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _records(path: Path) -> list[dict]:
    frame = pd.read_csv(path)
    # NaN -> None so optional fields (e.g. lead_time_days) validate as missing.
    return frame.astype(object).where(frame.notna(), None).to_dict(orient="records")


def load_production_input(data_dir: Path = DEFAULT_DATA_DIR) -> ProductionInput:
    """Read materials/products/recipes/orders CSVs and capacity.json from ``data_dir``."""
    capacity = json.loads((data_dir / "capacity.json").read_text(encoding="utf-8"))
    capacity.pop("_note", None)
    return ProductionInput(
        materials=[Material(**r) for r in _records(data_dir / "materials.csv")],
        products=[Product(**r) for r in _records(data_dir / "products.csv")],
        recipes=[RecipeLine(**r) for r in _records(data_dir / "recipes.csv")],
        orders=[Order(**r) for r in _records(data_dir / "orders.csv")],
        capacity=Capacity(**capacity),
    )
