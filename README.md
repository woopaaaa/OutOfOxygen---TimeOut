# Timed---TimeOut

Production planning engine for small food manufacturers (sample company: Kuih Mesra Sdn Bhd).

## Run

```
pip install -r requirements.txt
uvicorn core.api:app --host 0.0.0.0 --port 8000
```

Docs page: `/docs`. Tests: `pytest -v`.

## AI and forecasting

- `GET /forecast/sample`: weekly demand forecast with 80% range (predicts the Deepavali gift-box rush)
- `GET /stockout/sample`: when each material runs out and the last day to reorder
- `GET /insights/sample`: plan + forecast + stockouts + plain-English explanations in one call
- `POST /insights/ask`: ask a question in English or Bahasa Melayu

Optional: copy `.env.example` to `.env` and add a free Groq or Gemini key for AI-written briefings.
Without a key, built-in explanations are used. Details: `specs/07-forecasting.md`.
