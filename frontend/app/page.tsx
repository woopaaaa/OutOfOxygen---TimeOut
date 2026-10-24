import { getPlan } from "@/lib/planData";
import StatCard from "@/components/StatCard";

export default async function DashboardPage() {
  const plan = await getPlan();
  const metrics = plan.metrics.optimised;
  const ordersAtRisk = metrics.orders_late + metrics.orders_infeasible; //add the late orders with the one cannot be made
  const shortMaterials = plan.material_requirements.filter((m) => m.shortage > 0).length;
  const utilisationPercent = Math.round(metrics.utilisation * 100);
  const shortNames = plan.material_requirements
  .filter((m) => m.shortage > 0)
  .map((m) => m.name)
  .join(", ");
  return (
    <div>
      <h1 className="text-2xl font-bold">Factory's Health Dashboard</h1>
      <p className="mt-1 text-slate-600">A quick overview of orders, stock, capacity and costs.</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total orders" value={metrics.orders_total}/>
        <StatCard label="Orders at risk" value={ordersAtRisk} note=" are late or cannot be made" />
        <StatCard label="Materials stock low" value={shortMaterials}  note={`${shortNames} (out of ${plan.material_requirements.length})`} />
        <StatCard label="Capacity used" value={`${utilisationPercent}%`} note={`${metrics.hours_used} of ${metrics.hours_available} hours`} />
      </div>
      {plan.warnings.length > 0 && (
      <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-5">
        <h2 className="font-semibold text-red-800">Needs attention</h2>
        <ul className="mt-3 list-disc pl-5 text-sm text-red-700">
         {plan.warnings.map((warning) => ( //take the warning from output-example.json
         <li key={warning}>{warning}</li> //make a list for each warning
          ))}
        </ul>
    </div>
    )}
    </div>
  );
}
