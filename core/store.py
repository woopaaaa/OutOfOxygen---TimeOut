"""Module 10: SQLite storage (current data, purchase orders, activity log).

Uses only Python's built-in sqlite3, so there is nothing extra to install.
The database file is `timed.db` in the project folder. Set the environment
variable TIMED_DB to use a different file (the tests do this).
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi.encoders import jsonable_encoder

from core.loader import load_production_input
from core.models import ProductionInput

parent_dir = Path(__file__).parent.parent


def db_path() -> Path:
    return Path(os.environ.get("TIMED_DB", parent_dir / "timed.db"))


def connect() -> sqlite3.Connection:
    """Open the database (creating the tables the first time)."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            total_cost_rm REAL NOT NULL,
            request_json TEXT NOT NULL,
            decided_by TEXT,
            decided_at TEXT
        );
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            at TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT NOT NULL
        );
        """
    )
    return conn


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------- current data ----------

def save_dataset(data: ProductionInput) -> None:
    payload = json.dumps(jsonable_encoder(data))
    with connect() as conn:
        conn.execute(
            "INSERT INTO app_state (key, value) VALUES ('dataset', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (payload,),
        )


def load_dataset() -> tuple[ProductionInput, str]:
    """Return (data, source). source is "uploaded" or "sample"."""
    with connect() as conn:
        row = conn.execute("SELECT value FROM app_state WHERE key = 'dataset'").fetchone()
    if row is None:
        return load_production_input(), "sample"
    return ProductionInput.model_validate_json(row["value"]), "uploaded"


def reset_dataset() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM app_state WHERE key = 'dataset'")


# ---------- activity log ----------

def log_action(role: str, action: str, detail: str = "") -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO activity_log (at, actor_role, action, detail) VALUES (?, ?, ?, ?)",
            (now(), role, action, detail),
        )


def list_log(limit: int = 100) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, at, actor_role, action, detail FROM activity_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------- purchase orders ----------

def _purchase_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "status": row["status"],
        "total_cost_rm": row["total_cost_rm"],
        "decided_by": row["decided_by"],
        "decided_at": row["decided_at"],
        "request": json.loads(row["request_json"]),
    }


def create_purchase_order(request: dict) -> int:
    """Save a purchase request (always starts as pending_approval)."""
    request = jsonable_encoder(request)
    request["status"] = "pending_approval"
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO purchase_orders (created_at, status, total_cost_rm, request_json) VALUES (?, ?, ?, ?)",
            (now(), "pending_approval", request["total_cost_rm"], json.dumps(request)),
        )
        return cur.lastrowid


def list_purchase_orders() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM purchase_orders ORDER BY id DESC").fetchall()
    return [_purchase_row(r) for r in rows]


def get_purchase_order(order_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
    return _purchase_row(row) if row else None


def decide_purchase_order(order_id: int, new_status: str, role: str) -> dict:
    """Move a pending purchase order to approved/rejected. Raises ValueError if not pending."""
    order = get_purchase_order(order_id)
    if order is None:
        raise KeyError(order_id)
    if order["status"] != "pending_approval":
        raise ValueError(f"Purchase order {order_id} is already {order['status']}")
    request = order["request"]
    request["status"] = new_status
    with connect() as conn:
        conn.execute(
            "UPDATE purchase_orders SET status = ?, request_json = ?, decided_by = ?, decided_at = ? WHERE id = ?",
            (new_status, json.dumps(request), role, now(), order_id),
        )
    return get_purchase_order(order_id)