//  in the production plan
export type ScheduleLine = {
  order_id: string;
  customer: string;
  product_id: string;
  quantity: number;
  due_date: string;
  status: "on_time" | "late" | "infeasible";
  start_hour: number | null;
  end_hour: number | null;
  material_cost_rm: number;
  reason: string;
};
// how much is needed vs in stock
export type MaterialLine = {
  material_id: string;
  name: string;
  unit: string;
  required: number;
  in_stock: number;
  shortage: number;
  purchase_quantity: number;
  unit_cost_rm: number;
  purchase_cost_rm: number;
  lead_time_days: number | null;
};
//  thing to buy
export type PurchaseLine = {
  material_id: string;
  name: string;
  unit: string;
  quantity: number;
  unit_cost_rm: number;
  cost_rm: number;
};

//  shopping list that the owner must approve
export type PurchaseRequest = {
  status: string;
  requires_role: string;
  lines: PurchaseLine[];
  total_cost_rm: number;
};
// summary of numbers for one way of planning
export type MetricSet = {
  orders_total: number;
  orders_on_time: number;
  orders_late: number;
  orders_infeasible: number;
  on_time_rate: number;
  total_material_cost_rm: number;
  hours_used: number;
  hours_available: number;
  utilisation: number;
};

//  whole answer from the backend
export type PlanResult = {
  generated_at: string;
  planning_start: string;
  schedule: ScheduleLine[];
  material_requirements: MaterialLine[];
  purchase_request: PurchaseRequest;
  metrics: {
    baseline: MetricSet;
    optimised: MetricSet;
  };
  warnings: string[];
  assumptions: string[];
};
