# Trip Budget Calculator — CampusSolve Project #51

A Python application for estimating and tracking transport, stay, food and activity costs for trips.

## Requirements coverage

| PDF requirement | Implementation |
|---|---|
| Interactive terminal interface | `cli.py` provides a menu-driven terminal workflow |
| Defensive input validation | `core.py` validates required text, dates, traveler count and non-negative costs |
| Core calculation engine | `calculate_total()` and `summarize()` in `core.py` |
| Local persistence | `data_manager.py` reads/writes both `data/trips.csv` and `data/trips.json` |
| Record query & search | Streamlit Trip Records page and CLI keyword search |
| Executive summary | Dashboard and Analytics & Reports page |
| Multi-format export (stretch) | CSV, Markdown and TXT download buttons |
| Threshold warnings (stretch) | Over-budget warnings on dashboard |
| GUI (stretch) | Streamlit web interface |
| Bulk CSV import (stretch) | Row-by-row validation and error report |

## Setup (Windows 11)

1. Extract the ZIP file.
2. Open Command Prompt in the extracted `Trip_Budget_Calculator` folder.
3. (Recommended) Create and activate a virtual environment:

```bat
python -m venv .venv
.venv\Scripts\activate
```

4. Install dependencies:

```bat
python -m pip install -r requirements.txt
```

5. Start the Streamlit interface:

```bat
python -m streamlit run app.py
```

Streamlit will open the application in your browser. If it does not, open the local URL printed in the terminal (usually `http://localhost:8501`).

## Run the required terminal menu

```bat
python cli.py
```

## Data files

- `data/trips.csv` — active CSV records
- `data/trips.json` — active JSON records
- `data/sample_trips.csv` and `data/sample_trips.json` — 40 example records

The first launch includes sample trips so the dashboard and analytics are populated. New records are automatically saved to both active files. Back up the `data` folder before replacing or resetting the project.

## Bulk CSV format

Required columns: `trip_name,destination,start_date,end_date,travelers,transport,stay,food,activities`

Optional columns: `budget_limit,notes`

Dates must use `YYYY-MM-DD`. Costs must be numeric and non-negative. Invalid rows are skipped and shown in an import error table; valid rows are retained.

## Notes

- All cost values are treated as Indian Rupees (₹).
- A budget limit of `0` means no budget threshold is set.
- The app is designed for local use and uses local files; no external database or API is required.
