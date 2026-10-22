# Module 2: `core/loader.py` (read the data files)

**Goal:** turn the files in `data/` into one validated `ProductionInput`.
This is the **connected data** step of the Domain 2 journey: pull together the business's
stock, recipes, orders and capacity, so the planner has everything in one place.

**Done when:** `pytest tests/test_loader.py -v` is all green, and `pytest` (all tests) is still green.

## What to write

One function:

| Name | Input | Output |
|---|---|---|
| `load_production_input` | `data_dir` (a `pathlib.Path`), **optional** | a `ProductionInput` |

If `data_dir` is not given, it uses the project's `data/` folder.

## Which files it reads

| File | Becomes |
|---|---|
| `materials.csv` | list of `Material` |
| `products.csv` | list of `Product` |
| `recipes.csv` | list of `RecipeLine` |
| `orders.csv` | list of `Order` |
| `capacity.json` | one `Capacity` |

The column names in each CSV are the same as the field names in your models.

## Rules

1. **Default folder.** Find the `data/` folder from the **location of `loader.py`**, not from the folder
   the program happens to run from. (Test: the loader still works after changing the current directory.)
   Look up `pathlib.Path` and `__file__`.
2. **Empty cells mean "missing".** In `materials.csv`, an empty `lead_time_days` cell must become `None`.
   Watch out: if you use pandas, it reads empty cells as `NaN` (a float), not `None`, and Pydantic will reject
   `NaN` for an `int | None` field. Python's built-in `csv` module reads empty cells as `""`. Either way,
   you have to turn "empty" into `None` yourself.
3. **Extra keys in `capacity.json` are ignored.** The file has a `"_note"` key that isn't a `Capacity` field.
   It must not cause an error. (Two ways to handle it: remove it before building `Capacity`, or tell Pydantic
   to ignore unknown keys. Which is safer?)
4. **Missing file → `FileNotFoundError`**, and the message must contain the **file name**
   (e.g. `orders.csv`), so the user knows which file to add.
5. **Bad data is NOT your job here.** Don't check for negative stock, unknown products and so on.
   Build the models and let `ProductionInput` raise its `ValidationError`. Module 1 already does that.

## Tools you may need
- `pathlib.Path`: joining paths with `/`, `.exists()`, `.read_text()`
- `json.loads` or `json.load`
- either `csv.DictReader` (built in) or `pandas.read_csv` (already in `requirements.txt`)

## Think about (judges may ask)
- Why keep the loader separate from the models? (Hint: later the data might come from the frontend
  or a database instead of CSV files. What would have to change?)
- Why load from files at all, if the API will receive JSON? (Hint: demo, tests, and swapping in a real
  business's spreadsheet.)
