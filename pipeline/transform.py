import re
from datetime import datetime

SKILLS = [
    "Python", "SQL", "Java", "JavaScript", "TypeScript", "R", "C++", "Go", "Scala",
    "pandas", "NumPy", "TensorFlow", "PyTorch", "Spark", "Kafka", "Airflow", "dbt",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "Snowflake", "BigQuery",
    "FastAPI", "Django", "Flask", "REST", "GraphQL",
    "React", "Node.js", "Next.js", "Vue", "Angular", "HTML", "CSS",
    "Git", "Linux", "Tableau", "Power BI",
]

# Pre-compile patterns once; use word boundaries to avoid partial matches
_SKILL_PATTERNS = {
    skill: re.compile(rf"\b{re.escape(skill)}\b", re.IGNORECASE)
    for skill in SKILLS
}


def transform_jobs(raw_jobs: list) -> list:
    cleaned = []
    for job in raw_jobs:
        if not job.get("id") or not job.get("title"):
            continue

        cleaned.append({
            **job,
            "title": job["title"].strip().title(),
            "company": (job.get("company") or "").strip(),
            "location": (job.get("location") or "").strip(),
            "description": (job.get("description") or "").strip(),
            "date_posted": _parse_datetime(job.get("date_posted")),
        })

    return cleaned


def parse_skills(jobs: list) -> list:
    skill_records = []
    for job in jobs:
        description = job.get("description") or ""
        job_id = job["id"]

        for skill, pattern in _SKILL_PATTERNS.items():
            if pattern.search(description):
                skill_records.append({
                    "job_id": job_id,
                    "skill_name": skill,
                    "frequency": 1,
                })

    return skill_records


def _parse_datetime(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


if __name__ == "__main__":
    from pipeline.extract import fetch_jobs

    raw = fetch_jobs()
    jobs = transform_jobs(raw)
    skills = parse_skills(jobs)

    print(f"Cleaned jobs:   {len(jobs)}")
    print(f"Skill records:  {len(skills)}")
