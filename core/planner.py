import datetime
from core.inventory import InventoryLedger, build_recipe_index, requirements_for, material_cost

def working_hours_until(capacity, due_date):
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    current = capacity.planning_start
    total_hours = 0
    while current <= due_date:
        if days[current.weekday()] in capacity.working_days:
            total_hours = total_hours + capacity.hours_per_day
        current = current + datetime.timedelta(days=1)
    return total_hours

def production_hours(order, products):
    ph = order.quantity / products[order.product_id].units_per_hour
    return ph

def edd_sequence(orders):
    #edd = earliest due date fir
    return sorted(orders, key=lambda o: (o.due_date, o.order_id))

def baseline_sequence(orders):
    return orders.copy()

def plan_orders(data, sequence):
    #data = productionInput
    ledger = InventoryLedger(data.materials)
    recipe_index = build_recipe_index(data.recipes)
    products = {p.product_id : p for p in data.products}
    materials = {m.material_id: m for m in data.materials}
    schedule = []
    clock = 0

    for order in sequence:
        needs = requirements_for(order.product_id, order.quantity, recipe_index)
        missing = ledger.missing_for(needs)
        order_info = {
            "order_id": order.order_id,
            "customer": order.customer,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "due_date": order.due_date,
        }
        if missing:
            line = {
                **order_info,
                "status" : "infeasible",
                "start_hour" : None,
                "end_hour" : None,
                "material_cost_rm" : 0,
                "missing_materials" : missing,
                "reason" : "Not enough " + ", ".join(f"{materials[m].name} (short {amount} {materials[m].unit})" for m, amount in missing.items()
                ),
            }
            schedule.append(line)
            continue

        ledger.allocate(needs)
        start = clock
        end = round(start + production_hours(order, products), 2)
        clock = end
        available = working_hours_until(data.capacity, order.due_date)
        if end > available:
            status = "late"
            reason = "Finishes after the deadline (late)"
        else:
            status = "on_time"
            reason = "Enough materials and finishes before the deadline"
        line = {
            **order_info,
            "status" : status,
            "start_hour" : start,
            "end_hour" : end,
            "material_cost_rm" : material_cost(needs, materials),
            "missing_materials" : {},
            "reason" : reason
                    }
        schedule.append(line)
    return {
        "schedule" : schedule,
        "remaining_stock" : ledger.snapshot(),
        "hours_used" : clock

    }
def build_baseline_plan(data):
    return plan_orders(data, baseline_sequence(data.orders))


def build_optimised_plan(data):
    return plan_orders(data, edd_sequence(data.orders))

    




