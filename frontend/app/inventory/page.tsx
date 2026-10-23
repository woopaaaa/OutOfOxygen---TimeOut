import {plan} from "@/lib/planData";

export default function InventoryPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Inventory Intelligence</h1>
      <p className="mt-1 text-slate-600">
        See which materials are running low and what to reorder.
      </p>

      <div className="mt-6 space-y-3">
        {plan.material_requirements.map((m) => { //let for each materal be m
        const isShort = m.shortage > 0; 
        const percentage = Math.min(100, Math.round((m.in_stock / m.required) * 100 ));

        return (
          <div key={m.material_id} className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex justify-between text-sm">
              <span className="font-semibold">{m.name}</span>
              <span className={isShort ? "text-red-600" : "text-emerald-600"}>  {/*change color to red when short, green when enough */}
                {isShort ? `Short ${m.shortage} ${m.unit}` : "Enough"} {/*showing the text*/}
              </span>
            </div>
            <div className="mt-2 h-3 rounded-full bg-slate-200">
              <div className={`h-3 rounded-full ${isShort ? "bg-red-500" : "bg-emerald-500"}`}style={{ width: `${percentage}%` }}/>  {/*making the bar*/}
           </div>
           <p className="mt-1 text-xs text-slate-500">
                {m.in_stock} of {m.required} {m.unit} in stock ({percentage}%) {/*additional text*/}
              </p>
            </div>
          );
        })}

      </div>

    </div>
  );
}
