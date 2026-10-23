from core.planner import build_baseline_plan, build_optimised_plan, working_hours_until


def plan_metrics(plan, data):
    schedule = plan["schedule"]
    orders_total = len(schedule)

    orders_on_time = 0
    orders_late = 0
    orders_infeasible = 0
    total_material_cost = 0
    for line in schedule:
        if line["status"] == "on_time":
            orders_on_time += 1
        elif line["status"] == "late":
            orders_late += 1
        else:
            orders_infeasible += 1
        total_material_cost += line["material_cost_rm"]

    if orders_total > 0:
        on_time_rate = round(orders_on_time / orders_total, 2)
    else:
        on_time_rate = 0

    last_due_date = max(order.due_date for order in data.orders)
    hours_available = working_hours_until(data.capacity, last_due_date)
    hours_used = plan["hours_used"]
    if hours_available > 0:
        utilisation = round(hours_used / hours_available, 2)
    else:
        utilisation = 0

    return {
        "orders_total": orders_total,
        "orders_on_time": orders_on_time,
        "orders_late": orders_late,
        "orders_infeasible": orders_infeasible,
        "on_time_rate": on_time_rate,
        "total_material_cost_rm": round(total_material_cost, 2),
        "hours_used": hours_used,
        "hours_available": hours_available,
        "utilisation": utilisation,
    }


def compare_plans(data):
    return {
        "baseline": plan_metrics(build_baseline_plan(data), data),
        "optimised": plan_metrics(build_optimised_plan(data), data),
    }
