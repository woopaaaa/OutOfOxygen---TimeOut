from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.inventory import build_recipe_index, material_report, total_requirements
from core.loader import load_production_input
from core.models import ProductionInput
from core.planner import build_optimised_plan

ASSUMPTIONS = [
    "One production line: orders are made one after another",
    "No partial orders: an order is made in full or not at all",
    "Purchased materials are not counted as arriving within this plan",
]


def build_response(data):
    plan = build_optimised_plan(data)
    materials = {m.material_id: m for m in data.materials}
    recipe_index = build_recipe_index(data.recipes)
    totals = total_requirements(data.orders, recipe_index)
    report = material_report(totals, materials)
    lines = []
    for r in report:
        if r["purchase_quantity"] > 0:
            line = {
                "material_id" : r["material_id"],
                "name" : r["name"],
                "unit"	: r["unit"],
                "quantity"	: r["purchase_quantity"],
                "unit_cost_rm" : r["unit_cost_rm"],
                "cost_rm" : r["purchase_cost_rm"]
            }
            lines.append(line)

    warnings = [
        f"Order {s['order_id']} cannot be made: {s['reason']}"
        for s in plan["schedule"]
        if s["status"] == "infeasible"
    ]
    return {
        "generated_at": datetime.now().isoformat(),
        "planning_start": data.capacity.planning_start,
        "schedule": plan["schedule"],
        "material_requirements": report,
        "purchase_request": {
            "status": "pending_approval",
            "requires_role": "owner",
            "lines": lines,
            "total_cost_rm": round(sum(line["cost_rm"] for line in lines), 2),
        },
        "metrics": None,  # filled in by the metrics module (module 5)
        "warnings": warnings,
        "assumptions": ASSUMPTIONS,
    }


app = FastAPI(title="Timed", description="Production planning engine for small food manufacturers")

# Let the Next.js frontend (another address) call this API from the browser.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/plan/sample")
def plan_sample():
    return build_response(load_production_input())


@app.post("/plan")
def plan(data: ProductionInput):
    return build_response(data)
