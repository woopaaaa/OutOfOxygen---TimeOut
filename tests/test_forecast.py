"""Module 7 tests. See specs/07-forecasting.md."""

import csv
from datetime import date

import pandas as pd
import pytest

from core.forecast import (
    build_forecast, calendar_features, forecast_to_orders, load_calendar, load_sales_history, write_forecast_csv,
)


@pytest.fixture(scope="module")
def result():
    return build_forecast(4)


def by_key(result):
    return {(r["week_start"], r["product_id"]): r for r in result["forecast"]}


def test_calendar_features_match_history_columns():
    history, calendar = load_sales_history(), load_calendar()
    for row in history.to_dict("records"):
        features = calendar_features(row["week_start"], calendar)
        assert features["school_holiday"] == row["school_holiday"]
        assert features["ramadan"] == row["ramadan"]
        expected_event = row["festive_event"] if isinstance(row["festive_event"], str) else None
        assert features["festive_event"] == expected_event
        if expected_event:
            assert features["weeks_to_event"] == int(row["weeks_to_event"])


def test_one_row_per_product_per_week(result):
    assert result["history_end"] == date(2026, 10, 12)
    assert len(result["forecast"]) == 4 * 3
    weeks = sorted({r["week_start"] for r in result["forecast"]})
    assert weeks == [date(2026, 10, 19), date(2026, 10, 26), date(2026, 11, 2), date(2026, 11, 9)]


def test_interval_contains_forecast(result):
    for r in result["forecast"]:
        assert 0 < r["lower_80"] <= r["forecast_units"] <= r["upper_80"]


def test_predicts_deepavali_gift_box_rush(result):
    rows = by_key(result)
    for product in ("COOKIE_BTR", "KUIH_KELAPA"):
        week_before = rows[(date(2026, 10, 26), product)]
        week_after = rows[(date(2026, 11, 9), product)]
        assert week_before["change_vs_last_4_weeks_pct"] > 50
        assert week_before["forecast_units"] > 1.5 * week_after["forecast_units"]
        assert any("Deepavali" in d["driver"] for d in week_before["drivers"])
    # curry puffs are not a festive gift item
    assert abs(rows[(date(2026, 10, 26), "CURRY_PUFF")]["change_vs_last_4_weeks_pct"]) < 20


def test_handles_data_quality_issues(result):
    notes = " ".join(result["data_quality"])
    assert "KUIH_KELAPA" in notes and "2025-08-18" in notes
    assert "COOKIE_BTR" in notes and "2025-04-28" in notes


def test_beats_naive_baselines(result):
    for product, scores in result["backtest"]["products"].items():
        assert scores["model_mape"] < scores["naive_last_4_weeks_mape"], product
        assert scores["model_mape"] < scores["seasonal_naive_mape"], product
        assert scores["model_mape"] < 0.15, product
        assert 0.6 <= scores["interval_80_coverage"] <= 0.95, product


def test_contract_csv(tmp_path, result):
    path = tmp_path / "forecast.csv"
    write_forecast_csv(result["forecast"], path)
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0]) == ["week_start", "product_id", "forecast_units", "lower_80", "upper_80"]
    assert len(rows) == 12


def test_forecast_to_orders(result):
    orders = forecast_to_orders(result["forecast"])
    assert len(orders) == 12
    first = orders[0]
    assert first.due_date == date(2026, 10, 25)  # end of the week starting 2026-10-19
    high = forecast_to_orders(result["forecast"], scenario="upper_80")
    assert sum(o.quantity for o in high) > sum(o.quantity for o in orders)
