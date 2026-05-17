# Job Market Tracker

An ETL pipeline that pulls US job postings from the Adzuna API, cleans and stores them in MySQL, and serves real-time insights through a FastAPI backend and browser dashboard.

<!-- Add a screenshot here once the dashboard is running -->

---

## What It Does

1. **Extract** — Fetches job postings for 5 roles (software engineer, data engineer, data analyst, AI engineer, backend developer) across 5 pages of results from the Adzuna API
2. **Transform** — Cleans titles, normalizes dates, and parses in-demand skills from job descriptions using regex matching against a curated skills list
3. **Load** — Inserts cleaned jobs and skill records into MySQL; logs each run as a snapshot
4. **Serve** — FastAPI exposes four read-only endpoints; a single-page dashboard visualizes the data with Chart.js

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
│   └── schema.sql          # Run this first — creates the database and tables
├── pipeline/
│   ├── extract.py          # Pulls job data from Adzuna API
│   ├── transform.py        # Cleans data and parses skills from descriptions
│   └── load.py             # Inserts into MySQL; run this to populate the DB
├── api/
│   └── main.py             # FastAPI app with 4 endpoints + serves the dashboard
├── frontend/
│   └── index.html          # Single-page dashboard (no build step)
├── start.py                # One-command launcher — starts server + opens browser
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
This creates the `job_market_tracker` database and all three tables.

---

## Running the Pipeline

```bash
python3 -m pipeline.load
```

This runs the full ETL — extract → transform → load. It fetches 5 job titles × 5 pages × 50 results and inserts them into MySQL. Expect it to take 1–2 minutes.

---

## Launching the Dashboard

```bash
python3 start.py      # macOS / Linux
python start.py       # Windows
```

Starts the API server and opens `http://127.0.0.1:8000` in your default browser automatically. Press `Ctrl-C` to stop.

---

## API Endpoints

| Endpoint | Params | Description |
|---|---|---|
| `GET /skills/trending` | `limit` (default 10) | Top skills by total appearance frequency |
| `GET /skills/valuable` | `limit` (default 10) | Top skills by avg max salary (min. 10 jobs) |
| `GET /jobs/search` | `skill` (required) | Jobs matching a specific skill |
| `GET /salaries/by-role` | — | Avg salary range per job title |

Interactive docs available at `http://127.0.0.1:8000/docs` when the server is running.
