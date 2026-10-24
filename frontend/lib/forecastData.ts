import type { ForecastResult } from "./types";

const FORECAST_URL = "http://localhost:8000/forecast/sample";

export async function getForecast(): Promise<ForecastResult | null> {
  try {
    const response = await fetch(FORECAST_URL);
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as ForecastResult;
  } catch {
    return null;
  }
}
