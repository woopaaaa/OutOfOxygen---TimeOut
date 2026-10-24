from datetime import datetime
from typing import Literal

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from core.explain import ask, build_facts, explain
from core.forecast import build_forecast
from core.inventory import build_recipe_index, material_report, total_requirements
from core.loader import load_production_input
from core.metrics import compare_plans
from core.models import ProductionInput
from core.planner import build_optimised_plan
from core.stockout import predict_stockouts

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
        "metrics": compare_plans(data),
        "warnings": warnings,
        "assumptions": ASSUMPTIONS,
    }


app = FastAPI(title="Timed", description="Production planning engine for small food manufacturers")

# Let the Next.js frontend (another address) call this API from the browser.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/plan/sample")
def plan_sample():
    return build_response(load_production_input())

# to give the frontend the labels of choices in the frontend
@app.get("/input/sample") #name of the api
def input_sample(): 
    return load_production_input()


@app.post("/plan")
def plan(data: ProductionInput):
    return build_response(data)


# ---------- AI and forecasting (modules 7-9) ----------

class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    language: Literal["en", "ms"] = "en"


def build_insights(data, weeks=4, language="en"):
    plan = build_response(data)
    forecast = build_forecast(weeks)
    stockout = predict_stockouts(data, forecast["forecast"])
    facts = build_facts(plan, forecast, stockout)
    return {
        "plan": plan,
        "forecast": forecast,
        "stockout": stockout,
        "explanations": explain(facts, language),
    }


@app.get("/forecast/sample")
def forecast_sample(weeks: int = Query(4, ge=1, le=12)):
    return build_forecast(weeks)


@app.get("/stockout/sample")
def stockout_sample(weeks: int = Query(4, ge=1, le=12)):
    forecast = build_forecast(weeks, with_backtest=False)
    return predict_stockouts(load_production_input(), forecast["forecast"])


@app.get("/insights/sample")
def insights_sample(weeks: int = Query(4, ge=1, le=12), language: Literal["en", "ms"] = "en"):
    return build_insights(load_production_input(), weeks, language)


@app.post("/insights/ask")
def insights_ask(body: Question):
    data = load_production_input()
    plan = build_response(data)
    forecast = build_forecast(4, with_backtest=False)
    facts = build_facts(plan, forecast, predict_stockouts(data, forecast["forecast"]))
    return ask(body.question, facts, body.language)
