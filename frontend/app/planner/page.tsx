import {plan} from "@/lib/planData";
//text to show for each of the status
const statusLabel = {
  on_time: "On time",
  late: "Late",
  infeasible: "Cannot be made",
};
//set the color
const statusColor = {
  on_time: "bg-emerald-100 text-emerald-700",
  late: "bg-amber-100 text-amber-700",
  infeasible: "bg-red-100 text-red-700",
};


export default function PlannerPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Smart Production Planner</h1>
      <p className="mt-1 text-slate-600">
        Orders in the recommended production order.
      </p>

      <div className="mt-6 space-y-3">
        {plan.schedule.map((line, index) => ( //set the order
          <div key={line.order_id} className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-semibold">
                  {index + 1}. {line.order_id} · {line.customer}
                </p>
                <p className="text-sm text-slate-600">
                  {line.quantity} × {line.product_id} · due {line.due_date}
                </p>
              </div>
              <span className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold ${statusColor[line.status]}`}>
                {statusLabel[line.status]}
              </span>
            </div>

            {line.start_hour !== null && (
              <p className="mt-2 text-sm text-slate-600">
                Production time: hour {line.start_hour} to {line.end_hour}
              </p>
            )}

            <p className="mt-2 text-sm text-slate-500">{line.reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
