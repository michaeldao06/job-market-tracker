# Job Market Tracker

## Project Context
ETL pipeline portfolio project. Pulls job data from Adzuna API,
transforms with pandas, stores in MySQL, serves via FastAPI.
Schema-first approach — db/schema.sql drives all downstream decisions.

## Stack
Python, MySQL, FastAPI, pandas, requests, schedule,
mysql-connector-python, python-dotenv, uvicorn

## Project Structure
job-market-tracker/
├── db/schema.sql          # Design this first — it drives everything
├── pipeline/
│   ├── extract.py         # Adzuna API pulls
│   ├── transform.py       # pandas cleaning
│   └── load.py            # MySQL inserts
├── api/main.py            # FastAPI endpoints
├── .env                   # Never commit this
└── .gitignore

## DB Tables
- jobs: raw posting data (title, company, salary, location, date)
- skills: parsed skills + frequency counts
- snapshots: point-in-time captures for trend tracking

## API Endpoints
- GET /skills/trending
- GET /jobs/search?skill=
- GET /salaries/by-role

## Rules
- Never commit .env (API keys + DB credentials live there)
- Always use parameterized queries — no raw string SQL
- Check db/schema.sql before writing any queries or inserts
- Repo stays private until complete