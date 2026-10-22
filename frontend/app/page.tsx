import { plan } from "@/lib/planData";
import StatCard from "@/components/StatCard";

export default function DashboardPage() {
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
    </div>
  );
}
