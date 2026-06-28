# Job Market Tracker

An ETL pipeline that pulls US job postings from the Adzuna API, cleans and stores them in MySQL, and serves real-time insights through a FastAPI backend and browser dashboard.

![Dashboard](assets/dashboard.png)

---

## What It Does

1. **Extract** — Fetches job postings for 5 roles (software engineer, data engineer, data analyst, AI engineer, backend developer) across 5 pages of results from the Adzuna API
2. **Transform** — Cleans titles, normalizes dates, and parses in-demand skills from job descriptions using regex matching against a curated skills list
3. **Load** — Inserts cleaned jobs and de-duplicated skill records into MySQL; logs each run as a snapshot, overall and per-skill
4. **Serve** — FastAPI exposes five read-only endpoints; a single-page dashboard visualizes the data with Chart.js, including a skill-demand time series

---

## Tech Stack

- **Python 3.9+** — pipeline and API
- **FastAPI + uvicorn** — API server
- **MySQL** — data storage
- **pandas** — data transformation
- **mysql-connector-python** — database driver
- **Chart.js** — frontend charts
- **python-dotenv** — credential management

---

## Project Structure

```
job-market-tracker/
├── db/
│   ├── schema.sql          # Run this first — creates the database and tables
│   └── migrations/         # One-time, re-runnable upgrades for existing databases
├── pipeline/
│   ├── extract.py          # Pulls job data from Adzuna API
│   ├── transform.py        # Cleans data and parses skills from descriptions
│   └── load.py             # Inserts into MySQL; run this to populate the DB
├── api/
│   └── main.py             # FastAPI app with 5 endpoints + serves the dashboard
├── frontend/
│   └── index.html          # Single-page dashboard (no build step)
├── refresh.py              # Runs pipeline + starts server + opens browser (fresh data)
├── serve.py                # Starts server + opens browser only (data already loaded)
└── .env                    # Your credentials (never committed)
```

---

## Prerequisites

- Python 3.9 or higher
- MySQL running locally
- Free Adzuna API credentials — sign up at [developer.adzuna.com](https://developer.adzuna.com)

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/michaeldao06/job-market-tracker.git
cd job-market-tracker
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Create a `.env` file** in the project root with your credentials:
```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
DB_HOST=localhost
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=job_market_tracker
```

**4. Set up the database**
```bash
mysql -u root -p < db/schema.sql
```
This creates the `job_market_tracker` database and all four tables. For a database created before a schema change, apply the matching script in `db/migrations/` instead — each one is safe to re-run.

---

## Running the Project

**`refresh.py` — first time setup or data refresh**
```bash
python3 refresh.py      # macOS / Linux
python refresh.py       # Windows
```
Runs the full ETL pipeline (extract → transform → load), then starts the API server and opens the dashboard automatically. Use this when you want fresh data. The pipeline takes 1–2 minutes before the browser opens.

**`serve.py` — quick launch when data is already loaded**
```bash
python3 serve.py        # macOS / Linux
python serve.py         # Windows
```
Skips the pipeline entirely — starts the server and opens the browser in ~2 seconds. Use this for day-to-day access when you don't need to re-pull data.

**Pipeline only — no server**
```bash
python3 -m pipeline.run
```

Press `Ctrl-C` to stop the server.

---

## API Endpoints

| Endpoint | Params | Description |
|---|---|---|
| `GET /skills/trending` | `limit` (default 10) | Top skills by total appearance frequency |
| `GET /skills/valuable` | `limit` (default 10) | Top skills by avg max salary (min. 10 jobs) |
| `GET /skills/timeseries` | `skill` (required) | Active postings mentioning a skill over time (one point per run) |
| `GET /jobs/search` | `skill` (required) | Jobs matching a specific skill |
| `GET /salaries/by-role` | — | Avg salary range per job title |

Interactive docs available at `http://127.0.0.1:8000/docs` when the server is running.
