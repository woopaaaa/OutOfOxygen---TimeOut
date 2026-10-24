import type { ProductionInput } from "./types";

const INPUT_URL = "http://localhost:8000/input/sample";
export async function getInput(): Promise<ProductionInput | null> {
  try {
    const response = await fetch(INPUT_URL);
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as ProductionInput;
  } catch {
    return null;
  }
}
