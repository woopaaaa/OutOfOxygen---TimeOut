import type { PlanResult } from "./types"; //take the label with data type "PlanResult" that was exported from from types.ts
import exampleJson from "@/data/output-example.json";
const API_URL = "http://localhost:8000/plan/sample";

export async function getPlan(): Promise<PlanResult> {
  try {
    const response = await fetch(API_URL);
    if (!response.ok) {
      throw new Error(`API answered ${response.status}`);
    }
    return (await response.json()) as PlanResult;
  } catch (error) {
    console.warn("Backend not reachable, using example data instead:", error);
    return exampleJson as PlanResult;
  }
}

