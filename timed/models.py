"""Input data models for Timed.

All quantities are in the material's or product's own unit (kg, pcs, box...).
All money is in Malaysian Ringgit (RM).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Weekday = Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class Material(BaseModel):
    """A raw material held in inventory."""

    material_id: str = Field(min_length=1)
    name: str
    unit: str
    quantity_in_stock: float = Field(ge=0)
    unit_cost_rm: float = Field(ge=0)
    min_stock: float = Field(default=0, ge=0)
    lead_time_days: int | None = Field(default=None, ge=0)


class Product(BaseModel):
    """A finished product the factory makes."""

    product_id: str = Field(min_length=1)
    name: str
    unit: str
    units_per_hour: float = Field(gt=0, description="Production line throughput.")


class RecipeLine(BaseModel):
    """Material needed to make ONE unit of a product (bill of materials row)."""

    product_id: str
    material_id: str
    quantity_per_unit: float = Field(gt=0)


class Order(BaseModel):
    """A customer order for one product."""

    order_id: str = Field(min_length=1)
    customer: str
    product_id: str
    quantity: int = Field(gt=0)
    due_date: date


class Capacity(BaseModel):
    """Factory working-time capacity over the planning horizon."""

    planning_start: date
    hours_per_day: float = Field(gt=0, le=24)
    working_days: list[Weekday] = Field(min_length=1)


class ProductionInput(BaseModel):
    """Everything the planner needs. Cross-references are validated on construction."""

    materials: list[Material] = Field(min_length=1)
    products: list[Product] = Field(min_length=1)
    recipes: list[RecipeLine] = Field(min_length=1)
    orders: list[Order] = Field(min_length=1)
    capacity: Capacity

    @model_validator(mode="after")
    def _check_references(self) -> "ProductionInput":
        errors: list[str] = []
        material_ids = [m.material_id for m in self.materials]
        product_ids = [p.product_id for p in self.products]
        order_ids = [o.order_id for o in self.orders]
        for label, ids in (("material_id", material_ids), ("product_id", product_ids), ("order_id", order_ids)):
            duplicates = sorted({i for i in ids if ids.count(i) > 1})
            if duplicates:
                errors.append(f"Duplicate {label}: {duplicates}")

        known_materials, known_products = set(material_ids), set(product_ids)
        recipe_keys: set[tuple[str, str]] = set()
        for line in self.recipes:
            if line.product_id not in known_products:
                errors.append(f"Recipe references unknown product '{line.product_id}'")
            if line.material_id not in known_materials:
                errors.append(f"Recipe references unknown material '{line.material_id}'")
            key = (line.product_id, line.material_id)
            if key in recipe_keys:
                errors.append(f"Duplicate recipe line {key}")
            recipe_keys.add(key)

        products_with_recipe = {line.product_id for line in self.recipes}
        for order in self.orders:
            if order.product_id not in known_products:
                errors.append(f"Order {order.order_id} references unknown product '{order.product_id}'")
            elif order.product_id not in products_with_recipe:
                errors.append(f"Missing information: product '{order.product_id}' has no recipe")

        if errors:
            raise ValueError("; ".join(errors))
        return self
