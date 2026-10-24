"""Module 8: stockout predictions. See specs/07-forecasting.md.

Walks the material stock forward day by day over the forecast horizon,
burning what the forecast demand (and the confirmed orders) will use,
and reports when each material runs out and the last day to reorder.
"""

from datetime import timedelta

from core.inventory import build_recipe_index, requirements_for

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SCENARIOS = {"expected": "forecast_units", "high": "upper_80"}
REORDER_SOON_DAYS = 2  # order-by date within this many days of today counts as "reorder now"


def working_days_of(week_start, capacity, from_day=None):
    days = [week_start + timedelta(days=i) for i in range(7)]
    return [d for d in days if DAYS[d.weekday()] in capacity.working_days and (from_day is None or d >= from_day)]


def weekly_demand(forecast_rows, orders, scenario):
    """Units per (week_start, product). Confirmed orders are part of demand, so take the larger of the two."""
    column = SCENARIOS[scenario]
    demand = {(r["week_start"], r["product_id"]): r[column] for r in forecast_rows}
    confirmed = {}
    for o in orders:
        key = (o.due_date - timedelta(days=o.due_date.weekday()), o.product_id)
        confirmed[key] = confirmed.get(key, 0) + o.quantity
    for key, qty in confirmed.items():
        if key in demand:
            demand[key] = max(demand[key], qty)
    return demand


def daily_material_use(data, forecast_rows, scenario):
    """List of (day, {material_id: amount}) for every working day from planning_start to the horizon end."""
    recipe_index = build_recipe_index(data.recipes)
    demand = weekly_demand(forecast_rows, data.orders, scenario)
    start = data.capacity.planning_start
    weeks = sorted({w for w, _ in demand})
    out = []
    for week in weeks:
        all_days = working_days_of(week, data.capacity)
        days = working_days_of(week, data.capacity, from_day=start)
        if not days:
            continue
        use = {}
        for (w, product_id), units in demand.items():
            if w != week or product_id not in recipe_index:
                continue
            for m, amount in requirements_for(product_id, units, recipe_index).items():
                use[m] = use.get(m, 0) + amount / len(all_days)
        for day in days:
            out.append((day, use))
    return out


def run_out_day(stock, daily_use, material_id):
    """First working day on which the stock cannot cover that day's use, or None. Also returns total use."""
    left, total, day_out = stock, 0.0, None
    for day, use in daily_use:
        need = use.get(material_id, 0)
        total += need
        if day_out is None and need > left + 1e-9:
            day_out = day
        left -= need
    return day_out, total


def predict_stockouts(data, forecast_rows):
    start = data.capacity.planning_start
    usage = {s: daily_material_use(data, forecast_rows, s) for s in SCENARIOS}
    horizon_end = max((d for d, _ in usage["expected"]), default=start)

    materials = []
    for m in data.materials:
        expected_day, expected_total = run_out_day(m.quantity_in_stock, usage["expected"], m.material_id)
        high_day, high_total = run_out_day(m.quantity_in_stock, usage["high"], m.material_id)
        if expected_total == 0 and high_total == 0:
            continue
        lead = m.lead_time_days if m.lead_time_days is not None else 0
        order_by = expected_day - timedelta(days=lead) if expected_day else None

        if expected_day is None:
            status = "watch" if high_day else "ok"
        elif order_by < start:
            status = "critical"
        elif (order_by - start).days <= REORDER_SOON_DAYS:
            status = "reorder_now"
        else:
            status = "reorder_soon"

        working_days = len(usage["expected"])
        daily = expected_total / working_days if working_days else 0
        materials.append({
            "material_id": m.material_id,
            "name": m.name,
            "unit": m.unit,
            "in_stock": m.quantity_in_stock,
            "avg_daily_use": round(daily, 2),
            "days_of_cover": round(m.quantity_in_stock / daily, 1) if daily else None,
            "stockout_date": expected_day,
            "stockout_date_high_demand": high_day,
            "lead_time_days": m.lead_time_days,
            "order_by": order_by,
            "status": status,
            "need_until_horizon": round(expected_total, 2),
            "recommended_order_qty": round(max(0, expected_total + m.min_stock - m.quantity_in_stock), 2),
            "recommended_order_qty_high_demand": round(max(0, high_total + m.min_stock - m.quantity_in_stock), 2),
            "recommended_order_cost_rm": round(max(0, expected_total + m.min_stock - m.quantity_in_stock) * m.unit_cost_rm, 2),
        })

    rank = {"critical": 0, "reorder_now": 1, "reorder_soon": 2, "watch": 3, "ok": 4}
    materials.sort(key=lambda r: (rank[r["status"]], r["stockout_date"] or horizon_end, r["material_id"]))

    recipe_index = build_recipe_index(data.recipes)
    by_id = {r["material_id"]: r for r in materials}
    products = []
    for p in data.products:
        limits = [by_id[mid] for mid in recipe_index.get(p.product_id, {}) if mid in by_id and by_id[mid]["stockout_date"]]
        if limits:
            first = min(limits, key=lambda r: (r["stockout_date"], r["days_of_cover"] or 0))
            products.append({
                "product_id": p.product_id,
                "name": p.name,
                "production_stops_on": first["stockout_date"],
                "limiting_material": first["material_id"],
                "all_short_materials": sorted(r["material_id"] for r in limits),
            })
    products.sort(key=lambda r: r["production_stops_on"])

    warnings = [
        f"{m.name}: supplier lead time unknown, assumed 0 days"
        for m in data.materials
        if m.lead_time_days is None and m.material_id in by_id
    ]
    return {
        "as_of": start,
        "horizon_end": horizon_end,
        "materials": materials,
        "products_at_risk": products,
        "warnings": warnings,
        "assumptions": [
            "Weekly demand = the larger of the forecast and the confirmed orders due that week",
            "Demand is spread evenly over the working days of each week",
            "No purchases arrive unless they are ordered; pending purchase requests are not counted",
            "High-demand scenario uses the upper end of the 80% forecast interval",
        ],
    }
