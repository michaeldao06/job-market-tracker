from pipeline.extract import fetch_jobs
from pipeline.transform import transform_jobs, parse_skills
from pipeline.load import load


def run_pipeline():
    """Runs the full ETL pipeline: extract → transform → load."""

    print("=== Step 1: Extract ===")
    raw = fetch_jobs()

    print("\n=== Step 2: Transform ===")
    jobs   = transform_jobs(raw)
    skills = parse_skills(jobs)
    print(f"Cleaned jobs: {len(jobs)} | Skill records: {len(skills)}")

    print("\n=== Step 3: Load ===")
    load(jobs, skills)

    print("\nPipeline complete.")


if __name__ == "__main__":
    run_pipeline()
