import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (API credentials live there)
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Base URL for Adzuna's US job search endpoint — page number gets appended at request time
BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search"

# Job titles to search for — each one gets its own set of paginated requests
JOB_TITLES = [
    "software engineer",
    "data engineer",
    "data analyst",
    "AI engineer",
    "backend developer",
]

PAGES = 5             # How many pages to fetch per job title
RESULTS_PER_PAGE = 50 # Adzuna's max results per page


def fetch_jobs() -> list[dict]:
    """Fetches job listings from Adzuna for all job titles and returns them as a list of dicts."""
    all_jobs = []
    # Stamp the pull time once so every job in this run shares the same date_pulled
    date_pulled = datetime.now()

    for title in JOB_TITLES:
        for page in range(1, PAGES + 1):
            print(f"Fetching: '{title}' — page {page}/{PAGES}")

            # Query params sent with every request — credentials + search config
            params = {
                "app_id": APP_ID,
                "app_key": APP_KEY,
                "results_per_page": RESULTS_PER_PAGE,
                "what": title,           # The job title search term
                "content-type": "application/json",
            }

            try:
                # Page number is part of the URL path, not a query param
                response = requests.get(
                    f"{BASE_URL}/{page}", params=params, timeout=10
                )
                # Raises an HTTPError if the status code is 4xx or 5xx
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                # Log the error and skip this page rather than crashing the whole run
                print(f"  Error on '{title}' page {page}: {e}")
                continue

            # "results" is the list of job objects returned by the API
            for job in data.get("results", []):
                all_jobs.append(_parse_job(job, date_pulled))

    print(f"\nDone. Total jobs fetched: {len(all_jobs)}")
    return all_jobs


def _parse_job(job: dict, date_pulled: datetime) -> dict:
    """Extracts only the fields we need from a raw Adzuna job object."""
    return {
        "id": job.get("id"),
        "title": job.get("title"),
        # Adzuna nests company and location as objects — we only want the display string
        "company": job.get("company", {}).get("display_name"),
        "location": job.get("location", {}).get("display_name"),
        "salary_min": _to_int(job.get("salary_min")),
        "salary_max": _to_int(job.get("salary_max")),
        # Adzuna returns this as 0 or 1 — default to 0 (not predicted) if missing
        "salary_is_predicted": int(job.get("salary_is_predicted", 0)),
        "contract_type": job.get("contract_type"),   # e.g. "permanent", "contract"
        "contract_time": job.get("contract_time"),   # e.g. "full_time", "part_time"
        "category": job.get("category", {}).get("label"),
        "description": job.get("description"),
        "date_posted": job.get("created"),  # Raw ISO string — transform.py will clean this
        "date_pulled": date_pulled.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _to_int(value):
    """Safely converts salary values to int — Adzuna sometimes returns floats or strings."""
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    jobs = fetch_jobs()
    if jobs:
        print(f"\nSample record:\n{jobs[0]}")
