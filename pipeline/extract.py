import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search"

JOB_TITLES = [
    "software engineer",
    "data engineer",
    "data analyst",
    "AI engineer",
    "backend developer",
]

PAGES = 5
RESULTS_PER_PAGE = 50


def fetch_jobs() -> list[dict]:
    all_jobs = []
    date_pulled = datetime.now()

    for title in JOB_TITLES:
        for page in range(1, PAGES + 1):
            print(f"Fetching: '{title}' — page {page}/{PAGES}")

            params = {
                "app_id": APP_ID,
                "app_key": APP_KEY,
                "results_per_page": RESULTS_PER_PAGE,
                "what": title,
                "content-type": "application/json",
            }

            try:
                response = requests.get(
                    f"{BASE_URL}/{page}", params=params, timeout=10
                )
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                print(f"  Error on '{title}' page {page}: {e}")
                continue

            for job in data.get("results", []):
                all_jobs.append(_parse_job(job, date_pulled))

    print(f"\nDone. Total jobs fetched: {len(all_jobs)}")
    return all_jobs


def _parse_job(job: dict, date_pulled: datetime) -> dict:
    return {
        "id": job.get("id"),
        "title": job.get("title"),
        "company": job.get("company", {}).get("display_name"),
        "location": job.get("location", {}).get("display_name"),
        "salary_min": _to_int(job.get("salary_min")),
        "salary_max": _to_int(job.get("salary_max")),
        "salary_is_predicted": int(job.get("salary_is_predicted", 0)),
        "contract_type": job.get("contract_type"),
        "contract_time": job.get("contract_time"),
        "category": job.get("category", {}).get("label"),
        "description": job.get("description"),
        "date_posted": job.get("created"),
        "date_pulled": date_pulled.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _to_int(value) -> int | None:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    jobs = fetch_jobs()
    if jobs:
        print(f"\nSample record:\n{jobs[0]}")
