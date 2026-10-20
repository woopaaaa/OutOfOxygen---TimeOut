# Timed — Production Optimisation Engine (MVP)

Optimisation & analytics module for small Malaysian food manufacturers. Supports SDG 8 & 9.

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
pytest -q
```

## Layout
- `data/` — illustrative CSV/JSON sample data (replaceable)
- `timed/models.py` — Pydantic input schema + cross-reference validation
- `timed/loader.py` — CSV/JSON -> `ProductionInput`
- `timed/inventory.py` — requirements, cost, shortages, purchase quantities, allocation ledger
- `tests/` — pytest suite
