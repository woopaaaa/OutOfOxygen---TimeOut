import type { ProductionInput } from "./types";

const INPUT_URL = "http://localhost:8000/data";
export async function getInput(): Promise<ProductionInput | null> {
  try {
    const response = await fetch(INPUT_URL);
    if (!response.ok) {
      return null;
    }
    const answer = await response.json();
    return answer.data as ProductionInput;
  } catch {
    return null;
  }
}
