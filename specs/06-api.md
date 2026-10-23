# Module 6: `core/api.py` (let your teammates call the engine)

**Goal:** a small web API so the backend and frontend can ask the engine for a plan over HTTP
and get back the JSON described in `specs/output-contract.md`.
Without this, your code only runs on your laptop. With it, the whole team's app can use it.

**Done when:** `pytest tests/test_api.py -v` is all green, all other tests still pass, and the
server runs with:

```
uvicorn core.api:app --reload
```

Then open http://127.0.0.1:8000/docs in a browser. FastAPI makes an interactive page for free.

## Part A: `build_response(data)` (a normal function, no web stuff)

Input: a `ProductionInput`. Output: a dict shaped like `specs/output-contract.md`.
Keep all the logic here, so it can be tested without a server.

| Key | How to get it |
|---|---|
| `generated_at` | the current date and time as an ISO text, e.g. `datetime.now().isoformat()` |
| `planning_start` | from `data.capacity` |
| `schedule` | the **optimised** plan's schedule |
| `material_requirements` | `material_report(...)` of what **all** orders need (`total_requirements`) |
| `purchase_request` | see below |
| `metrics` | `None` for now. Module 5 fills this in later |
| `warnings` | one text per **infeasible** order in the schedule, containing its `order_id` and its reason |
| `assumptions` | a short list of texts (one line, no partial orders, purchases don't arrive within the plan) |

### `purchase_request`

| Key | Value |
|---|---|
| `status` | `"pending_approval"` (the engine only **recommends**, a person approves) |
| `requires_role` | `"owner"` |
| `lines` | one dict per material line with `purchase_quantity > 0`, with keys `material_id, name, unit, quantity, unit_cost_rm, cost_rm` |
| `total_cost_rm` | sum of the lines' `cost_rm`, rounded to 2 |

Worked example: in the material report, butter has `purchase_quantity` 9.2 and `purchase_cost_rm` 257.6.
Its purchase line is `{"material_id": "BUTTER", "name": "Butter", "unit": "kg", "quantity": 9.2, "unit_cost_rm": 28.0, "cost_rm": 257.6}`.
Flour with `purchase_quantity` 0 would get **no** line.

## Part B: the web app (FastAPI)

| Method + path | Does |
|---|---|
| `GET /health` | returns `{"status": "ok"}`. Teammates use it to check the server is up |
| `GET /plan/sample` | loads the files in `data/` and returns `build_response(...)` |
| `POST /plan` | the request body **is** a `ProductionInput` (JSON). Returns `build_response(...)` of it |

Rules:
- If the body is invalid (e.g. an unknown product), FastAPI must answer **422** with the errors.
  You get this for free by typing the parameter as `ProductionInput`. Your module 1 checks run automatically.
- **CORS:** the frontend runs on a different address (Next.js, port 3000), and browsers block that
  unless the API allows it. Add FastAPI's `CORSMiddleware` allowing all origins for now.
  (Before a real launch, you'd list only your own frontend's address.)
- Dates in the response come out as text like `"2026-10-23"`. FastAPI converts them for you.

## Tools
- FastAPI tutorial, "First Steps" and "Request Body": https://fastapi.tiangolo.com/tutorial/
- CORS: https://fastapi.tiangolo.com/tutorial/cors/
- The tests use FastAPI's `TestClient`, which calls your app without starting a real server.

## For your teammates (put this in the README when it works)
- Run: `uvicorn core.api:app --host 0.0.0.0 --port 8000`
- On Replit, use the same command as the run command.
- Docs page: `/docs`. Example request body: the contents of the `data/` files, as JSON.

## Think about (judges may ask)
- Why keep `build_response` separate from the route functions?
- Why does the engine set `status` to `"pending_approval"` instead of buying anything?
