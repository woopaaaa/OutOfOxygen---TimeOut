

def build_recipe_index(recipes):
    out_dictionary = {}
    for m in recipes:
        if m.product_id not in out_dictionary:
            out_dictionary[m.product_id] = {}
        out_dictionary[m.product_id][m.material_id] = m.quantity_per_unit
    return out_dictionary
    
def requirements_for(product_id, quantity, recipe_index):
    recipe = recipe_index[product_id]
    amount_required = {key: round(value * quantity, 4) for key, value in recipe.items()}
    return amount_required

def total_requirements(orders, recipe_index):
    totals = {}
    
    for order in orders:
        needs = requirements_for(order.product_id, order.quantity, recipe_index)
        for material, amount in needs.items():
            if material not in totals:
                totals[material] = 0
            totals[material] += amount
    return {key: round(value, 4) for key, value in totals.items()}

def material_cost(requirements, materials):
    total_cost = 0
    for material_id, amount in requirements.items():
        total_cost += amount * materials[material_id].unit_cost_rm
    return round(total_cost, 2)
        
def material_report(requirements, materials):
    report = []
    for material_id, amount in sorted(requirements.items()):
        m = materials[material_id]
        shortage = round(max(0, amount - m.quantity_in_stock), 4)
        purchase_quantity = round(max(0, amount + m.min_stock - m.quantity_in_stock), 4)
        purchase_cost_rm = round(purchase_quantity * m.unit_cost_rm, 2)
        line = {

            "material_id" : material_id, 
            "name" : m.name, 
            "unit" : m.unit, 
            "required" : amount, 
            "in_stock" : m.quantity_in_stock, 
            "shortage" : shortage, 
            "purchase_quantity" : purchase_quantity, 
            "unit_cost_rm" : m.unit_cost_rm, 
            "purchase_cost_rm" : purchase_cost_rm, 
            "lead_time_days" : m.lead_time_days
            
            }
        report.append(line)
    return report

class InventoryLedger:
    def __init__(self, materials):
        self.stock = {m.material_id: m.quantity_in_stock for m in materials}

    def available(self, material_id):
        return ( self.stock[material_id])
    def snapshot(self):
        return self.stock.copy()
    def missing_for(self, needs):
        missing = {}
        for material_id, amount in needs.items():
            if amount > self.stock[material_id]:
                missing[material_id] = round(amount - self.stock[material_id], 4)
        return missing
    def allocate(self, needs):
        if self.missing_for(needs):
            return False
        for material_id, amount in needs.items():
            self.stock[material_id] = round(self.stock[material_id] - amount, 4)
        return True



            



            






        




