import { getForecast } from "@/lib/forecastData";
import { getInput } from "@/lib/inputData";

function formatWeek(date: string) {
  return new Date(date).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export default async function ForecastPage() {
  const forecast = await getForecast();
  const input = await getInput();

  if (!forecast) {
    return (
      <div>
        <h1 className="text-2xl font-bold">Demand Forecast</h1>
        <p className="mt-6 text-slate-500">Start the Python API to see the forecast.</p>
      </div>
    );
  }

  const weeks = [...new Set(forecast.forecast.map((line) => line.week_start))];
  const productIds = [...new Set(forecast.forecast.map((line) => line.product_id))];

  function productName(productId: string) {
    const product = input?.products.find((p) => p.product_id === productId);
    return product ? product.name : productId;
  }

  function findLine(week: string, productId: string) {
    return forecast!.forecast.find((line) => line.week_start === week && line.product_id === productId);
  }

  function weekNote(week: string) {
    const lineWithDriver = forecast!.forecast.find((line) => line.week_start === week && line.drivers.length > 0);
    return lineWithDriver ? lineWithDriver.drivers[0].driver : "";
  }

  const biggestJump = forecast.forecast.reduce((best, line) =>
    line.change_vs_last_4_weeks_pct > best.change_vs_last_4_weeks_pct ? line : best
  );

  return (
    <div>
      <h1 className="text-2xl font-bold">Demand Forecast</h1>
      <p className="mt-1 text-slate-600">
        Predicted sales for the next {forecast.horizon_weeks} weeks, based on past weekly sales.
      </p>

      <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900">
        Biggest increase: <b>{productName(biggestJump.product_id)}</b> in the week of{" "}
        <b>{formatWeek(biggestJump.week_start)}</b>, up{" "}
        <b>{biggestJump.change_vs_last_4_weeks_pct}%</b>
        {biggestJump.drivers.length > 0 && ` (${biggestJump.drivers[0].driver})`}. Prepare stock early.
      </div>

      <div className="mt-6 overflow-x-auto">
        <table className="w-full rounded-lg border border-slate-200 bg-white text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-slate-500">
              <th className="p-3">Week</th>
              {productIds.map((productId) => (
                <th key={productId} className="p-3">{productName(productId)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {weeks.map((week) => (
              <tr key={week} className="border-b border-slate-100 align-top">
                <td className="p-3">
                  <p className="font-medium">{formatWeek(week)}</p>
                  <p className="text-xs text-slate-500">{weekNote(week)}</p>
                </td>
                {productIds.map((productId) => {
                  const line = findLine(week, productId);
                  if (!line) {
                    return <td key={productId} className="p-3">-</td>;
                  }
                  const isUp = line.change_vs_last_4_weeks_pct >= 0;
                  return (
                    <td key={productId} className="p-3">
                      <span className="text-lg font-semibold">{line.forecast_units}</span>{" "}
                      <span className={isUp ? "text-emerald-600" : "text-red-600"}>
                        {isUp ? "▲" : "▼"}
                        {Math.abs(line.change_vs_last_4_weeks_pct)}%
                      </span>
                      <p className="text-xs text-slate-500">
                        ({line.lower_80} to {line.upper_80})
                      </p>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-slate-500">
        ▲ / ▼ compared with the last 4 weeks. The range in brackets is where sales will fall 80% of the time.
      </p>

      <h2 className="mt-8 text-lg font-semibold">How accurate is it?</h2>
      <p className="text-sm text-slate-600">
        Tested on past weeks the model did not see. Lower error is better.
      </p>
      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {productIds.map((productId) => {
          const test = forecast.backtest.products[productId];
          if (!test) {
            return null;
          }
          return (
            <div key={productId} className="rounded-lg border border-slate-200 bg-white p-4">
              <p className="font-semibold">{productName(productId)}</p>
              <p className="mt-2 text-sm">
                Our forecast error: <b className="text-emerald-700">{Math.round(test.model_mape * 100)}%</b>
              </p>
              <p className="text-sm text-slate-500">
                Simple guess error: {Math.round(test.naive_last_4_weeks_mape * 100)}%
              </p>
            </div>
          );
        })}
      </div>

      {forecast.data_quality.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold">Data notes</h2>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
            {forecast.data_quality.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
