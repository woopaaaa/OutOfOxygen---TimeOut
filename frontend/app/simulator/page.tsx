import { getPlan } from "@/lib/planData";
export default async function SimulatorPage() {
  const plan = await getPlan();
  const before = plan.metrics.baseline;
  const after = plan.metrics.optimised;
  const rows = [
    {
      label: "Orders on time",
      before: `${before.orders_on_time} of ${before.orders_total}`,
      after: `${after.orders_on_time} of ${after.orders_total}`,
    },
    {
      label: "On-time rate",
      before: `${Math.round(before.on_time_rate * 100)}%`,
      after: `${Math.round(after.on_time_rate * 100)}%`,
    },
    {
      label: "Orders that cannot be made",
      before: `${before.orders_infeasible}`,
      after: `${after.orders_infeasible}`,
    },
    {
      label: "Material cost",
      before: `RM ${before.total_material_cost_rm.toFixed(2)}`,
      after: `RM ${after.total_material_cost_rm.toFixed(2)}`,
    },
    {
      label: "Production hours used",
      before: `${before.hours_used} h`,
      after: `${after.hours_used} h`,
    },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold">Impact Simulator</h1>
      <p className="mt-1 text-slate-600">
        Normal plan (first come, first served) vs smart plan (earliest deadline first).
      </p>

      <table className="mt-6 w-full rounded-lg border border-slate-200 bg-white text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-slate-500">
            <th className="p-3"></th>
            <th className="p-3">Normal plan</th>
            <th className="p-3 text-emerald-700">Smart plan</th>
          </tr>
        </thead>
        <tbody>
          {/* loop all the tables */}
          {rows.map((row) => (
            <tr key={row.label} className="border-b border-slate-100">
              <td className="p-3 font-medium">{row.label}</td>
              <td className="p-3">{row.before}</td>
              <td className="p-3 font-semibold text-emerald-700">{row.after}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
