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

    def global_check(self):
        matCheck = []
        prodCheck = []
        orderCheck = []
        errors = []
        products_with_recipes = []


        for m in self.materials:
                    matCheck.append(m.material_id)
        for p in self.products:
                    prodCheck.append(p.product_id) 
        for o in self.orders:
                    orderCheck.append(o.order_id)
        def error_check(ids, label):
            errors = []
            seen = set()
            for item in ids:
                if item in seen:
                    errors.append(f"Duplicate {label}: {item}")
                else:
                    seen.add(item)
            return errors

        def known_check(ids, known, label):
            errors = []
            for item in ids:
                if item not in known:
                    errors.append(f"unknown {label} '{item}'")
            return errors
        
        for r in self.recipes:
            products_with_recipes.append(r.product_id)
            
        for order in self.orders:
            if order.product_id not in products_with_recipes:
                errors.append(f"Order product_id '{order.product_id}' contains Missing information, has no recipe")


        errors.extend(error_check([(r.material_id, r.product_id) for r in self.recipes], "recipe line"))      
        errors.extend(error_check(matCheck, "material_id"))
        errors.extend(error_check(prodCheck, "product_id"))
        errors.extend(error_check(orderCheck, "order_id"))
        errors.extend(known_check([r.material_id for r in self.recipes], matCheck, "material"))
        errors.extend(known_check([r.product_id for r in self.recipes], prodCheck, "product"))
        errors.extend(known_check([o.product_id for o in self.orders], prodCheck, "product"))



        if errors:
            raise ValueError("; ".join(errors))
        return self    
            
        
            

    

        


