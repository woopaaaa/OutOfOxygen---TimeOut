"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Order, ProductionInput } from "@/lib/types";

const DATA_URL = "http://localhost:8000/data";
const RESET_URL = "http://localhost:8000/data/reset";

type AddOrderFormProps = {
  input: ProductionInput;
};

export default function AddOrderForm({ input }: AddOrderFormProps) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function addOrder(formData: FormData) {
    setMessage("");
    setError("");

    const newOrder: Order = {
      order_id: `NEW-${input.orders.length + 1}`,
      customer: String(formData.get("customer")),
      product_id: String(formData.get("product_id")),
      quantity: Number(formData.get("quantity")),
      due_date: String(formData.get("due_date")),
    };

    const body = { ...input, orders: [...input.orders, newOrder] };

    try {
      const response = await fetch(DATA_URL, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        setError("The backend did not accept this order. Please check the values.");
        return;
      }
      setMessage(`Order ${newOrder.order_id} for ${newOrder.customer} was added to the plan.`);
      router.refresh();
    } catch {
      setError("Backend not reachable. Is the Python API running?");
    }
  }

  async function resetData() {
    setMessage("");
    setError("");
    try {
      const response = await fetch(RESET_URL, { method: "POST" });
      if (!response.ok) {
        setError("Could not reset the data.");
        return;
      }
      setMessage("All orders are back to the sample data.");
      router.refresh();
    } catch {
      setError("Backend not reachable. Is the Python API running?");
    }
  }

  return (
    <div className="mt-8 rounded-lg border border-slate-200 bg-white p-5">
      <h2 className="text-lg font-semibold">Add a new order</h2>
      <p className="text-sm text-slate-500">
        The order is saved and every page is planned again with it.
      </p>

      <form action={addOrder} className="mt-4 grid gap-3 sm:grid-cols-2">
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
          Add order
        </button>
      </form>

      {message && <p className="mt-4 text-sm text-emerald-700">{message}</p>}
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <button
        type="button"
        onClick={resetData}
        className="mt-4 text-sm text-slate-500 underline hover:text-slate-700"
      >
        Reset to sample data
      </button>
    </div>
  );
}
