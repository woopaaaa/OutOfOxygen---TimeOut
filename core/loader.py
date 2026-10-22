import csv
import json
from core.models import Capacity, Material, Order, Product, RecipeLine, ProductionInput
from pathlib import Path

parent_dir = Path(__file__).parent.parent
default_data_dir = parent_dir / "data"

def load_production_input(data_dir = default_data_dir):

    def read_csv_file(file_path, model_class):
        with open(file_path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [model_class(**{key: None if value == "" else value for key, value in row.items()}) for row in reader]
            
    materials = read_csv_file(data_dir / "materials.csv", Material)
    products = read_csv_file(data_dir / "products.csv", Product)
    recipes = read_csv_file(data_dir / "recipes.csv", RecipeLine)
    orders = read_csv_file(data_dir / "orders.csv", Order)
        
    with open(data_dir / "capacity.json", mode='r', encoding='utf-8') as f:
        capacity = json.load(f)
        capacity.pop("_note", None) 
        capacity_model = Capacity(**capacity)
        production_input = ProductionInput(**{
                            "materials": materials,
                            "products": products,
                            "recipes": recipes,
                            "orders": orders,
                            "capacity": capacity_model
                        })
                
        return production_input
        
        
    