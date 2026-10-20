from pydantic import BaseModel, Field, model_validator
from datetime import date
from typing import Literal

Weekday = Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

class Material(BaseModel):
    material_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    quantity_in_stock: float = Field(ge=0)
    unit_cost_rm: float = Field(ge=0)
    min_stock: float = Field(ge=0, default = 0)
    lead_time_days: int | None = Field(ge=0, default = None)

class Product(BaseModel):
    name : str = Field(min_length=1)
    unit: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    units_per_hour: float = Field(gt=0)

class RecipeLine(BaseModel):
    product_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    quantity_per_unit: float = Field(gt=0)

class Order(BaseModel):
    order_id: str = Field(min_length=1)
    customer: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    due_date: date

class Capacity(BaseModel):
    planning_start: date
    hours_per_day: float = Field(gt=0, le = 24)
    working_days: list[Weekday] = Field(min_length=1)

class ProductionInput(BaseModel):
    materials: list[Material] = Field(min_length=1)
    products: list[Product] = Field(min_length=1)
    recipes: list[RecipeLine] = Field(min_length=1)
    orders: list[Order] = Field(min_length=1)
    capacity: Capacity
    @model_validator(mode="after")
    def validate_materials(self):
        errors = []
        seen_material_ids = set()
        
        for m in self.materials:
            if m.material_id in seen_material_ids:
                errors.append(f"Duplicate material_id: {m.material_id}")
            else:
                seen_material_ids.add(m.material_id)
        if errors != []:
            raise ValueError(errors)
        return self

        


