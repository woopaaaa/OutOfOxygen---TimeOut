"""Module 7: weekly demand forecasting. See specs/07-forecasting.md.

One small model per product: a log-linear regression on calendar features
(trend, price, promo, school holiday, Ramadan, festival build-up), fitted with
ridge regularisation and a robust second pass so one-off bulk orders do not
inflate the forecast. No extra libraries: numpy + pandas only.
"""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from core.models import Order

parent_dir = Path(__file__).parent.parent
default_forecast_dir = parent_dir / "data" / "forecasting"

FESTIVAL_OFFSETS = [-3, -2, -1, 0, 1]
Z_80 = 1.2816  # two-sided 80% interval of a normal distribution
OUTLIER_CUTOFF = 3.5  # robust z-score above which a week is treated as a one-off
HOLDOUT_WEEKS = 26

FEATURE_LABELS = {
    "promo": "Promotion",
    "school_holiday": "School holiday",
    "ramadan": "Ramadan",
    "log_price": "Price change",
}


# ---------- data ----------

def load_sales_history(data_dir=default_forecast_dir):
    df = pd.read_csv(data_dir / "sales_history.csv", parse_dates=["week_start"])
    df["week_start"] = df["week_start"].dt.date
    return df


def load_calendar(data_dir=default_forecast_dir):
    df = pd.read_csv(data_dir / "calendar_events.csv", parse_dates=["date"])
    df["date"] = df["date"].dt.date
    return df


def monday_of(day):
    return day - timedelta(days=day.weekday())


def _periods(calendar, start_label, end_label):
    starts = sorted(calendar.loc[calendar["event"] == start_label, "date"])
    ends = sorted(calendar.loc[calendar["event"] == end_label, "date"])
    return list(zip(starts, ends))


def calendar_features(week_start, calendar):
    """School holiday / Ramadan / nearest festival for the week starting on week_start (a Monday)."""
    week_end = week_start + timedelta(days=6)

    def overlaps(periods):
        return int(any(start <= week_end and end >= week_start for start, end in periods))

    festivals = calendar[calendar["event_type"] == "festival"]
    best = None
    for _, row in festivals.iterrows():
        offset = (week_start - monday_of(row["date"])).days // 7
        if FESTIVAL_OFFSETS[0] <= offset <= FESTIVAL_OFFSETS[-1]:
            if best is None or abs(offset) < abs(best[1]):
                best = (row["event"], offset)

    return {
        "school_holiday": overlaps(_periods(calendar, "School holiday start", "School holiday end")),
        "ramadan": overlaps(_periods(calendar, "Ramadan start", "Ramadan end")),
        "festive_event": best[0] if best else None,
        "weeks_to_event": best[1] if best else None,
    }


def data_quality_report(history):
    """Missing weeks per product (the model skips them, nothing is filled in)."""
    notes = []
    all_weeks = pd.date_range(min(history["week_start"]), max(history["week_start"]), freq="7D").date
    for product_id, rows in history.groupby("product_id"):
        missing = sorted(set(all_weeks) - set(rows["week_start"]))
        for week in missing:
            notes.append(f"{product_id}: no sales row for week {week.isoformat()} (skipped, not filled in)")
    return notes


# ---------- model ----------

class ProductModel:
    """Log-linear ridge regression for one product's weekly units."""

    def __init__(self, product_id, origin, ref_price, festivals):
        self.product_id = product_id
        self.origin = origin  # week 0 of the trend
        self.ref_price = ref_price
        self.festivals = festivals
        self.columns = (
            ["intercept", "trend", "log_price", "promo", "school_holiday", "ramadan"]
            + [f"fest{o:+d}" for o in FESTIVAL_OFFSETS]
            + [f"{f}{o:+d}" for f in festivals for o in FESTIVAL_OFFSETS]
        )
        self.coef = None
        self.sigma = None
        self.outliers = []

    def design(self, rows):
        X = np.zeros((len(rows), len(self.columns)))
        index = {c: i for i, c in enumerate(self.columns)}
        for r, row in enumerate(rows):
            X[r, index["intercept"]] = 1
            X[r, index["trend"]] = (row["week_start"] - self.origin).days / 365.25
            X[r, index["log_price"]] = np.log(row["avg_price_rm"] / self.ref_price)
            for name in ("promo", "school_holiday", "ramadan"):
                X[r, index[name]] = row[name]
            event, offset = row.get("festive_event"), row.get("weeks_to_event")
            if isinstance(event, str) and offset is not None and not pd.isna(offset):
                X[r, index[f"fest{int(offset):+d}"]] = 1
                if f"{event}{int(offset):+d}" in index:
                    X[r, index[f"{event}{int(offset):+d}"]] = 1
        return X

    def _penalty(self):
        # Shared effects are barely penalised; festival-specific effects are shrunk
        # towards the shared festival curve because each festival appears only ~twice.
        p = np.full(len(self.columns), 0.01)
        p[0] = 0
        for i, c in enumerate(self.columns):
            if not (c.startswith("fest") or c in ("intercept", "trend", "log_price", "promo", "school_holiday", "ramadan")):
                p[i] = 1.0
        return np.diag(p)

    def _solve(self, X, y):
        return np.linalg.solve(X.T @ X + self._penalty(), X.T @ y)

    def fit(self, rows):
        X = self.design(rows)
        y = np.log(np.array([row["units_sold"] for row in rows], dtype=float))
        coef = self._solve(X, y)
        resid = y - X @ coef
        robust_sigma = 1.4826 * np.median(np.abs(resid - np.median(resid)))
        keep = np.abs(resid) <= OUTLIER_CUTOFF * max(robust_sigma, 1e-9)
        self.outliers = [rows[i] for i in np.where(~keep)[0]]
        self.coef = self._solve(X[keep], y[keep])
        resid = y[keep] - X[keep] @ self.coef
        dof = max(keep.sum() - np.linalg.matrix_rank(X[keep]), 1)
        self.sigma = float(np.sqrt(resid @ resid / dof))
        return self

    def predict(self, rows):
        X = self.design(rows)
        mean_log = X @ self.coef
        # exp(mean) is the median; the half-variance correction gives the mean.
        point = np.exp(mean_log + self.sigma ** 2 / 2)
        lower = np.exp(mean_log - Z_80 * self.sigma)
        upper = np.exp(mean_log + Z_80 * self.sigma)
        return point, lower, upper, X

    def drivers(self, x_row):
        """Multiplicative effects active in one design row, biggest first."""
        index = {c: i for i, c in enumerate(self.columns)}
        effects = {}
        for name in ("promo", "school_holiday", "ramadan", "log_price"):
            value = x_row[index[name]] * self.coef[index[name]]
            if abs(value) > 1e-9:
                effects[FEATURE_LABELS[name]] = value
        fest = [c for c in self.columns if c.startswith("fest") or any(c.startswith(f) for f in self.festivals)]
        festival_effect = sum(x_row[index[c]] * self.coef[index[c]] for c in fest)
        event = next((c for c in fest if x_row[index[c]] and not c.startswith("fest")), None)
        if event is None:
            event = next((c for c in fest if x_row[index[c]]), None)
        if event is not None:
            name, offset = event[:-2], int(event[-2:])
            name = "Festival" if name == "fest" else name
            if offset < 0:
                label = f"{name} in {-offset} week{'s' if offset < -1 else ''}"
            elif offset == 0:
                label = f"{name} week"
            else:
                label = f"Week after {name}"
            effects[label] = festival_effect
        out = [
            {"driver": label, "multiplier": round(float(np.exp(v)), 2)}
            for label, v in effects.items()
            if abs(np.exp(v) - 1) >= 0.03
        ]
        return sorted(out, key=lambda d: -abs(np.log(d["multiplier"])))


def _rows(df):
    return df.to_dict("records")


def fit_models(history, calendar):
    festivals = sorted(calendar.loc[calendar["event_type"] == "festival", "event"].unique())
    origin = min(history["week_start"])
    models = {}
    for product_id, rows in history.groupby("product_id"):
        ref_price = float(rows["avg_price_rm"].median())
        models[product_id] = ProductModel(product_id, origin, ref_price, festivals).fit(_rows(rows))
    return models


def future_rows(product_id, last_week, weeks, last_price, calendar):
    rows = []
    for i in range(1, weeks + 1):
        week_start = last_week + timedelta(weeks=i)
        rows.append({
            "week_start": week_start,
            "product_id": product_id,
            "avg_price_rm": last_price,
            "promo": 0,
            **calendar_features(week_start, calendar),
        })
    return rows


# ---------- backtest ----------

def mape(actual, predicted):
    actual, predicted = np.asarray(actual, float), np.asarray(predicted, float)
    return round(float(np.mean(np.abs(actual - predicted) / actual)), 3)


def backtest(history, calendar, holdout_weeks=HOLDOUT_WEEKS):
    """Train on everything except the last holdout_weeks, then score the model and two naive baselines."""
    cutoff = sorted(history["week_start"].unique())[-holdout_weeks]
    train, test = history[history["week_start"] < cutoff], history[history["week_start"] >= cutoff]
    models = fit_models(train, calendar)
    results = {}
    for product_id, rows in test.groupby("product_id"):
        rows = rows.sort_values("week_start")
        point, lower, upper, _ = models[product_id].predict(_rows(rows))
        actual = rows["units_sold"].to_numpy()
        past = train[train["product_id"] == product_id].set_index("week_start")["units_sold"]
        last_4 = float(past.sort_index().iloc[-4:].mean())
        seasonal = [past.get(w - timedelta(weeks=52), last_4) for w in rows["week_start"]]
        results[product_id] = {
            "weeks_tested": len(rows),
            "model_mape": mape(actual, point),
            "naive_last_4_weeks_mape": mape(actual, [last_4] * len(rows)),
            "seasonal_naive_mape": mape(actual, seasonal),
            "interval_80_coverage": round(float(np.mean((actual >= lower) & (actual <= upper))), 2),
        }
    return {"holdout_start": cutoff, "products": results}


# ---------- public API ----------

def build_forecast(weeks=4, data_dir=default_forecast_dir, with_backtest=True):
    """Forecast the next `weeks` weeks after the last week of sales history, for every product."""
    history = load_sales_history(data_dir)
    calendar = load_calendar(data_dir)
    models = fit_models(history, calendar)
    last_week = max(history["week_start"])

    rows = []
    for product_id, model in models.items():
        past = history[history["product_id"] == product_id].sort_values("week_start")
        recent_avg = float(past["units_sold"].iloc[-4:].mean())
        future = future_rows(product_id, last_week, weeks, float(past["avg_price_rm"].iloc[-1]), calendar)
        point, lower, upper, X = model.predict(future)
        for i, row in enumerate(future):
            rows.append({
                "week_start": row["week_start"],
                "product_id": product_id,
                "forecast_units": int(round(point[i])),
                "lower_80": int(round(lower[i])),
                "upper_80": int(round(upper[i])),
                "change_vs_last_4_weeks_pct": round((point[i] / recent_avg - 1) * 100),
                "festive_event": row["festive_event"],
                "weeks_to_event": row["weeks_to_event"],
                "drivers": model.drivers(X[i]),
            })
    rows.sort(key=lambda r: (r["week_start"], r["product_id"]))

    quality = data_quality_report(history)
    for model in models.values():
        for o in model.outliers:
            quality.append(
                f"{model.product_id}: week {o['week_start'].isoformat()} ({o['units_sold']} units) looks like a one-off "
                f"and was left out of the model"
            )

    return {
        "generated_at": datetime.now().isoformat(),
        "history_end": last_week,
        "horizon_weeks": weeks,
        "model": "Per-product log-linear ridge regression on trend, price, promo, school holiday, "
                 "Ramadan and festival build-up, with robust outlier removal",
        "forecast": rows,
        "backtest": backtest(history, calendar) if with_backtest else None,
        "data_quality": quality,
        "assumptions": [
            "No promotions are planned in the forecast weeks",
            "Prices stay at the last observed price",
            "Intervals assume errors look like the past (80% of weeks should fall inside)",
        ],
    }


def forecast_to_orders(rows, scenario="forecast_units"):
    """Turn forecast rows into planned Orders (due at the end of the week), as agreed with the planner."""
    return [
        Order(
            order_id=f"FC-{r['product_id']}-{r['week_start'].isoformat()}",
            customer="Forecast demand" if scenario == "forecast_units" else "Forecast demand (high)",
            product_id=r["product_id"],
            quantity=max(int(r[scenario]), 1),
            due_date=r["week_start"] + timedelta(days=6),
        )
        for r in rows
        if r[scenario] > 0
    ]


def write_forecast_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["week_start", "product_id", "forecast_units", "lower_80", "upper_80"])
        for r in rows:
            writer.writerow([r["week_start"].isoformat(), r["product_id"], r["forecast_units"], r["lower_80"], r["upper_80"]])


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Forecast weekly demand from data/forecasting/")
    parser.add_argument("--weeks", type=int, default=4)
    parser.add_argument("--csv", type=Path, help="also write the contract CSV here")
    args = parser.parse_args()
    result = build_forecast(args.weeks)
    if args.csv:
        write_forecast_csv(result["forecast"], args.csv)
    print(json.dumps(result, indent=2, default=str))
