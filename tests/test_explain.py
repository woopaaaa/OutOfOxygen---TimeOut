"""Module 9 tests. See specs/07-forecasting.md. No network: the LLM is replaced by fakes."""

import pytest
from fastapi.testclient import TestClient

import core.explain as explain_module
from core.api import app, build_response
from core.explain import ask, build_facts, explain, invented_numbers, llm_config
from core.forecast import build_forecast
from core.loader import load_production_input
from core.stockout import predict_stockouts

CONFIG = {"provider": "fake", "api_key": "x", "base_url": "http://fake", "model": "fake-model"}
client = TestClient(app)


@pytest.fixture(scope="module")
def facts():
    data = load_production_input()
    forecast = build_forecast(4, with_backtest=False)
    return build_facts(build_response(data), forecast, predict_stockouts(data, forecast["forecast"]))


@pytest.fixture(autouse=True)
def no_keys(monkeypatch):
    for name in ("LLM_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(explain_module, "load_dotenv", lambda *a, **k: None)


def test_template_without_key(facts):
    result = explain(facts)
    assert result["source"] == "template"
    assert "4 of 6" in result["summary"] and "3" in result["summary"]
    assert set(result["orders"]) == {f"ORD-00{i}" for i in range(1, 7)}
    assert "cannot be made" in result["orders"]["ORD-001"]
    assert "BUTTER" in result["stockout"]
    assert result["warnings"]


def test_llm_summary_used_when_numbers_check_out(facts):
    text = "4 of 6 orders are on time. ORD-001 is blocked by butter. Approve the purchase request."
    result = explain(facts, llm=lambda messages, config: text, config=CONFIG)
    assert result["source"] == "llm"
    assert result["summary"] == text
    assert result["model"] == "fake-model"


def test_llm_with_invented_number_is_rejected(facts):
    result = explain(facts, llm=lambda m, c: "You will make RM 98765 profit.", config=CONFIG)
    assert result["source"] == "template"
    assert "98765" in result["warnings"][0]


def test_llm_failure_falls_back(facts):
    def broken(messages, config):
        raise ConnectionError("down")
    result = explain(facts, llm=broken, config=CONFIG)
    assert result["source"] == "template"
    assert "ConnectionError" in result["warnings"][0]


def test_prompt_contains_facts_and_language(facts):
    seen = {}

    def spy(messages, config):
        seen["messages"] = messages
        return "ok"
    ask("Kenapa ORD-001 tidak dibuat?", facts, language="ms", llm=spy, config=CONFIG)
    assert "Bahasa Melayu" in seen["messages"][0]["content"]
    assert "ORD-001" in seen["messages"][1]["content"]


def test_number_guard_accepts_derived_forms(facts):
    assert invented_numbers("Butter runs out on 2026-10-22, order 128.68 kg.", facts) == []
    assert invented_numbers("on-time rate 67%", {"rate": 0.67}) == []
    assert invented_numbers("costs RM 1234.5", facts) == [1234.5]


def test_provider_selection(monkeypatch):
    assert llm_config() is None
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    assert llm_config()["provider"] == "gemini"
    monkeypatch.setenv("GROQ_API_KEY", "q")
    assert llm_config()["provider"] == "groq"
    monkeypatch.setenv("LLM_MODEL", "other")
    assert llm_config()["model"] == "other"


# ---------- endpoints ----------

def test_forecast_endpoint():
    body = client.get("/forecast/sample?weeks=2").json()
    assert len(body["forecast"]) == 6
    assert body["backtest"]["products"]


def test_stockout_endpoint():
    body = client.get("/stockout/sample").json()
    assert body["materials"][0]["status"] in ("critical", "reorder_now")


def test_insights_endpoint_without_key():
    body = client.get("/insights/sample").json()
    assert set(body) == {"plan", "forecast", "stockout", "explanations"}
    assert body["explanations"]["source"] == "template"


def test_ask_endpoint_without_key():
    body = client.post("/insights/ask", json={"question": "Why is ORD-001 not made?"}).json()
    assert body["answer"] is None and body["warnings"]
    assert client.post("/insights/ask", json={"question": "x"}).status_code == 422


def test_weeks_validated():
    assert client.get("/forecast/sample?weeks=99").status_code == 422
