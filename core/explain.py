"""Module 9: natural-language explanations. See specs/07-forecasting.md.

Every explanation is built from calculated facts. Plain-English templates always
work offline; if a free LLM key is configured (Groq, Gemini or OpenRouter, all via
their OpenAI-compatible endpoints) the LLM writes the owner's briefing and answers
questions. Any number in the LLM's text that is not in the facts is rejected and
the template text is used instead, so the AI cannot invent numbers.
"""

import json
import os
import re
import time
from pathlib import Path

import httpx

parent_dir = Path(__file__).parent.parent

PROVIDERS = {
    "groq": {"key_env": "GROQ_API_KEY", "base_url": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
    "gemini": {"key_env": "GEMINI_API_KEY", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "model": "gemini-flash-lite-latest"},
    "openrouter": {"key_env": "OPENROUTER_API_KEY", "base_url": "https://openrouter.ai/api/v1", "model": "meta-llama/llama-3.3-70b-instruct:free"},
}

LANGUAGES = {"en": "English", "ms": "Bahasa Melayu"}

SYSTEM_PROMPT = """You explain production-planning recommendations to the owner of a small Malaysian food factory.
Rules:
- Use ONLY the facts in the JSON you are given. Never invent, estimate or recalculate numbers.
- Copy numbers and dates exactly as they appear in the facts.
- The engine only recommends. Purchases need the owner's approval; never say anything was bought or sent.
- Plain words, short sentences, no jargon (say "forecast", not "regression"). Money is in RM.
- If the facts do not answer something, say so."""


# ---------- configuration ----------

def load_dotenv(path=parent_dir / ".env"):
    """Read KEY=value lines from .env into the environment (without overriding real env vars)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def llm_config():
    """Pick the first configured provider. LLM_API_KEY + LLM_BASE_URL + LLM_MODEL override everything."""
    load_dotenv()
    if os.environ.get("LLM_API_KEY"):
        groq = PROVIDERS["groq"]
        return {
            "provider": "custom",
            "api_key": os.environ["LLM_API_KEY"],
            "base_url": os.environ.get("LLM_BASE_URL", groq["base_url"]),
            "model": os.environ.get("LLM_MODEL", groq["model"]),
        }
    for name, p in PROVIDERS.items():
        if os.environ.get(p["key_env"]):
            return {
                "provider": name,
                "api_key": os.environ[p["key_env"]],
                "base_url": os.environ.get("LLM_BASE_URL", p["base_url"]),
                "model": os.environ.get("LLM_MODEL", p["model"]),
            }
    return None


def call_llm(messages, config, timeout=30, retries=1):
    body = {"model": config["model"], "messages": messages, "temperature": 0.2, "max_tokens": 4000}
    if config["provider"] == "gemini":
        body["reasoning_effort"] = "low"  # Gemini models "think" by default, which can take a minute
    for attempt in range(retries + 1):
        response = httpx.post(
            config["base_url"].rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {config['api_key']}"},
            json=body,
            timeout=timeout,
        )
        # free tiers answer 429/503 when busy: wait a moment and try once more
        if response.status_code in (429, 503) and attempt < retries:
            time.sleep(2)
            continue
        response.raise_for_status()
        choice = response.json()["choices"][0]
        if choice.get("finish_reason") == "length":
            raise ValueError("AI reply was cut off")
        return choice["message"]["content"].strip()


# ---------- facts ----------

def _fmt(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def build_facts(plan, forecast, stockout):
    """The only information the explanations (template or LLM) may use."""
    opt, base = plan["metrics"]["optimised"], plan["metrics"]["baseline"]
    return json.loads(json.dumps({
        "planning_start": plan["planning_start"],
        "plan": {
            "orders_total": opt["orders_total"],
            "on_time_optimised": opt["orders_on_time"],
            "on_time_first_come_first_served": base["orders_on_time"],
            "orders_late": opt["orders_late"],
            "orders_infeasible": opt["orders_infeasible"],
            "orders": [
                {k: s[k] for k in ("order_id", "customer", "product_id", "quantity", "due_date", "status", "reason", "missing_materials")}
                for s in plan["schedule"]
            ],
        },
        "purchase_request": {
            "status": plan["purchase_request"]["status"],
            "total_cost_rm": plan["purchase_request"]["total_cost_rm"],
            "lines": [
                {k: line[k] for k in ("material_id", "name", "unit", "quantity", "cost_rm")}
                for line in plan["purchase_request"]["lines"]
            ],
        },
        "forecast": [
            {k: r[k] for k in ("week_start", "product_id", "forecast_units", "lower_80", "upper_80",
                               "change_vs_last_4_weeks_pct", "drivers")}
            for r in forecast["forecast"]
        ],
        "forecast_data_quality": forecast["data_quality"],
        "stockout": [
            {k: m[k] for k in ("material_id", "name", "unit", "in_stock", "days_of_cover", "stockout_date",
                               "lead_time_days", "order_by", "status", "recommended_order_qty", "recommended_order_cost_rm")}
            for m in stockout["materials"]
            if m["status"] != "ok"
        ],
        "products_at_risk": stockout["products_at_risk"],
    }, default=_fmt))


# ---------- template explanations (always available) ----------

STATUS_WORDS = {
    "critical": "will run out before a new delivery can arrive, even if ordered today",
    "reorder_now": "needs to be reordered now",
    "reorder_soon": "should be reordered soon",
    "watch": "is fine on the expected forecast but could run out if demand is high",
}


def explain_order(o):
    if o["status"] == "on_time":
        return f"{o['order_id']} ({o['customer']}, {o['quantity']} {o['product_id']}) is planned to finish before its due date {o['due_date']}."
    if o["status"] == "late":
        return f"{o['order_id']} ({o['customer']}) will finish after its due date {o['due_date']}: there are not enough working hours before then."
    missing = ", ".join(f"{m} short by {q}" for m, q in o["missing_materials"].items())
    return (f"{o['order_id']} ({o['customer']}, due {o['due_date']}) cannot be made with current stock ({missing}). "
            f"Orders due earlier were given the materials first.")


def explain_forecast(r):
    drivers = ", ".join(f"{d['driver']} (x{d['multiplier']})" for d in r["drivers"]) or "normal trend only"
    direction = "up" if r["change_vs_last_4_weeks_pct"] >= 0 else "down"
    return (f"Week of {r['week_start']}: about {r['forecast_units']} {r['product_id']} "
            f"(likely between {r['lower_80']} and {r['upper_80']}), {direction} {abs(r['change_vs_last_4_weeks_pct'])}% "
            f"on the last 4 weeks. Drivers: {drivers}.")


def explain_stockout(m):
    if m["stockout_date"] is None:
        return f"{m['name']} {STATUS_WORDS['watch']}."
    lead = f"{m['lead_time_days']}-day" if m["lead_time_days"] is not None else "unknown"
    return (f"{m['name']}: {m['in_stock']} {m['unit']} in stock covers about {m['days_of_cover']} working days, "
            f"so it runs out on {m['stockout_date']}. With a {lead} supplier lead time it {STATUS_WORDS[m['status']]} "
            f"(order by {m['order_by']}). Suggested order: {m['recommended_order_qty']} {m['unit']} "
            f"(RM {m['recommended_order_cost_rm']}), pending owner approval.")


def template_summary(facts):
    p = facts["plan"]
    lines = [
        f"The plan makes {p['on_time_optimised']} of {p['orders_total']} orders on time "
        f"(first come, first served would make {p['on_time_first_come_first_served']}) by doing the most urgent orders first."
    ]
    blocked = [o for o in p["orders"] if o["status"] == "infeasible"]
    if blocked:
        lines.append("Cannot be made with current stock: " + ", ".join(o["order_id"] for o in blocked) + ".")
    pr = facts["purchase_request"]
    if pr["lines"]:
        lines.append(f"The purchase request (RM {pr['total_cost_rm']}) is waiting for the owner's approval.")
    rush = [r for r in facts["forecast"] if r["change_vs_last_4_weeks_pct"] >= 25]
    if rush:
        top = max(rush, key=lambda r: r["change_vs_last_4_weeks_pct"])
        lines.append(f"Demand is rising: {top['product_id']} is forecast at {top['forecast_units']} in the week of "
                     f"{top['week_start']}, up {top['change_vs_last_4_weeks_pct']}%"
                     + (f" ({top['drivers'][0]['driver']})." if top["drivers"] else "."))
    urgent = [m for m in facts["stockout"] if m["status"] in ("critical", "reorder_now")]
    if urgent:
        lines.append("Reorder now: " + ", ".join(f"{m['name']} (runs out {m['stockout_date']})" for m in urgent) + ".")
    return " ".join(lines)


def template_explanations(facts):
    return {
        "summary": template_summary(facts),
        "orders": {o["order_id"]: explain_order(o) for o in facts["plan"]["orders"]},
        "forecast": [explain_forecast(r) for r in facts["forecast"]],
        "stockout": {m["material_id"]: explain_stockout(m) for m in facts["stockout"]},
    }


# ---------- number guard ----------

NUMBER = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")


def _numbers(text):
    out = []
    for raw in NUMBER.findall(text):
        try:
            out.append(float(raw.replace(",", "")))
        except ValueError:
            pass
    return out


def allowed_numbers(facts):
    allowed = set(range(0, 13))  # small counts ("2 orders", "1 week") and months
    for v in _numbers(json.dumps(facts)):
        for x in (v, abs(v), v * 100, (v - 1) * 100, abs(v - 1) * 100):
            allowed.add(round(x))
            allowed.add(round(x, 1))
            allowed.add(round(x, 2))
    return allowed


def invented_numbers(text, facts):
    allowed = allowed_numbers(facts)
    return sorted({
        v for v in _numbers(text)
        if round(v, 2) not in allowed and round(v, 1) not in allowed and v not in allowed
    })


# ---------- public API ----------

def _ask_llm(task, facts, language, config, llm):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n- Answer in {LANGUAGES.get(language, 'English')}."},
        {"role": "user", "content": f"FACTS:\n{json.dumps(facts)}\n\nTASK: {task}"},
    ]
    return (llm or call_llm)(messages, config)


def explain(facts, language="en", llm=None, config=None):
    """Owner briefing + per-item explanations. `llm` can be swapped for a fake in tests."""
    result = {**template_explanations(facts), "source": "template", "model": None, "warnings": []}
    config = config or llm_config()
    if config is None:
        result["warnings"].append("No AI key configured (set GROQ_API_KEY or GEMINI_API_KEY): using built-in explanations")
        return result
    task = ("Write a briefing of at most 6 short sentences for the owner: what the plan achieves, which orders are at risk "
            "and why, what demand is coming and why, and what to reorder by when. End with what needs their approval.")
    try:
        text = _ask_llm(task, facts, language, config, llm)
    except Exception as e:  # network, quota, bad key: never break the plan
        result["warnings"].append(f"AI explanation unavailable ({type(e).__name__}): using built-in explanations")
        return result
    bad = invented_numbers(text, facts)
    if bad:
        result["warnings"].append(f"AI briefing mentioned numbers not in the data {bad}: using built-in explanation")
        return result
    result.update(summary=text, source="llm", model=config["model"])
    return result


def ask(question, facts, language="en", llm=None, config=None):
    """Answer an owner's free-text question, grounded in the facts."""
    config = config or llm_config()
    if config is None:
        return {"answer": None, "source": "none",
                "warnings": ["No AI key configured (set GROQ_API_KEY or GEMINI_API_KEY), so questions cannot be answered"]}
    try:
        text = _ask_llm(f"Answer the owner's question in at most 4 sentences: {question}", facts, language, config, llm)
    except Exception as e:
        return {"answer": None, "source": "none", "warnings": [f"AI unavailable ({type(e).__name__})"]}
    bad = invented_numbers(text, facts)
    if bad:
        return {"answer": None, "source": "none",
                "warnings": [f"AI answer mentioned numbers not in the data {bad}, so it was withheld"]}
    return {"answer": text, "source": "llm", "model": config["model"], "warnings": []}
