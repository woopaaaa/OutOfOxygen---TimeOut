"use client";

import { useState } from "react";
import type { Order, PlanResult, ProductionInput } from "@/lib/types";

const PLAN_URL = "http://localhost:8000/plan";

type AddOrderFormProps = {
  input: ProductionInput;
};

export default function AddOrderForm({ input }: AddOrderFormProps) {
  // Things that change on screen after the user clicks the button
  const [newPlan, setNewPlan] = useState<PlanResult | null>(null);
  const [error, setError] = useState("");

  // Runs when the form is submitted
  async function planWithNewOrder(formData: FormData) {
    setError("");

    // 1. Build the new order from what the user typed
    const newOrder: Order = {
      order_id: `NEW-${input.orders.length + 1}`,
      customer: String(formData.get("customer")),
      product_id: String(formData.get("product_id")),
      quantity: Number(formData.get("quantity")),
      due_date: String(formData.get("due_date")),
    };

    // 2. Same factory data, but with the new order added to the list
    const body = { ...input, orders: [...input.orders, newOrder] };

    // 3. Send it to the backend and show the answer
    try {
      const response = await fetch(PLAN_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        setError("The backend did not accept this order. Please check the values.");
        return;
      }
      setNewPlan(await response.json());
    } catch {
      setError("Backend not reachable. Is the Python API running?");
    }
  }

  return (
    <div className="mt-8 rounded-lg border border-slate-200 bg-white p-5">
      <h2 className="text-lg font-semibold">Try a new order</h2>

      <form action={planWithNewOrder} className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="text-sm">
          Customer
          <input name="customer" required className="mt-1 w-full rounded border border-slate-300 p-2" />
        </label>

        <label className="text-sm">
          Product
          <select name="product_id" className="mt-1 w-full rounded border border-slate-300 p-2">
            {input.products.map((product) => (
              <option key={product.product_id} value={product.product_id}>
                {product.name}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm">
          Quantity
          <input name="quantity" type="number" min="1" required className="mt-1 w-full rounded border border-slate-300 p-2" />
        </label>

        <label className="text-sm">
          Due date
          <input name="due_date" type="date" required className="mt-1 w-full rounded border border-slate-300 p-2" />
        </label>

        <button type="submit" className="rounded-lg bg-emerald-600 px-4 py-2 font-semibold text-white hover:bg-emerald-700 sm:col-span-2">
          Plan with this order
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      {newPlan && (
        <div className="mt-6">
          <h3 className="font-semibold">New plan</h3>
          <ul className="mt-2 space-y-1 text-sm">
            {newPlan.schedule.map((line, index) => (
              <li key={line.order_id}>
                {index + 1}. {line.order_id} · {line.customer} · <b>{line.status}</b> · {line.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
