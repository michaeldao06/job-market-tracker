import os
from datetime import datetime
from typing import Optional

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load DB credentials from .env
load_dotenv()


def get_connection():
    """Opens and returns a MySQL connection using credentials from .env."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def load(jobs: list, skills: list) -> None:
    """
    Main entry point. Inserts cleaned jobs and skill records into MySQL,
    then writes a snapshot row summarising this pipeline run.
    """
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        jobs_inserted = _insert_jobs(cursor, jobs)
        _insert_skills(cursor, skills)
        total_jobs = _get_total_jobs(cursor)
        _insert_snapshot(cursor, jobs_inserted, total_jobs)

        # Commit all inserts together — if anything above raised, we never reach here
        conn.commit()
        print(f"\nLoad complete.")
        print(f"  Jobs inserted this run : {jobs_inserted}")
        print(f"  Total jobs in DB       : {total_jobs}")
        print(f"  Skill records inserted : {len(skills)}")

    except Error as e:
        print(f"Database error: {e}")
        # Roll back any partial inserts so the DB stays consistent
        if conn:
            conn.rollback()

    finally:
        # Always close cursor and connection, even if an error occurred
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def _insert_jobs(cursor, jobs: list) -> int:
    """
    Inserts job records using INSERT IGNORE — existing IDs are silently skipped.
    Returns the count of rows actually inserted (not skipped).
    """
    sql = """
        INSERT IGNORE INTO jobs (
            id, title, company, location,
            salary_min, salary_max, salary_is_predicted,
            contract_type, contract_time,
            category, description, date_posted, date_pulled
        ) VALUES (
            %(id)s, %(title)s, %(company)s, %(location)s,
            %(salary_min)s, %(salary_max)s, %(salary_is_predicted)s,
            %(contract_type)s, %(contract_time)s,
            %(category)s, %(description)s, %(date_posted)s, %(date_pulled)s
        )
    """
    inserted = 0
    for job in jobs:
        cursor.execute(sql, job)
        # rowcount is 1 if the row was inserted, 0 if INSERT IGNORE skipped it
        inserted += cursor.rowcount

    print(f"Jobs processed: {len(jobs)} total, {inserted} new insertions")
    return inserted


def _insert_skills(cursor, skills: list) -> None:
    """
    Inserts skill records linked to their job via job_id.
    Skills are re-inserted each run — they're tied to jobs via ON DELETE CASCADE.
    """
    sql = """
        INSERT INTO skills (job_id, skill_name, frequency)
        VALUES (%(job_id)s, %(skill_name)s, %(frequency)s)
    """
    cursor.executemany(sql, skills)
    print(f"Skill records inserted: {len(skills)}")


def _get_total_jobs(cursor) -> int:
    """Queries the total number of rows in the jobs table after this run's inserts."""
    cursor.execute("SELECT COUNT(*) FROM jobs")
    result = cursor.fetchone()
    return result[0] if result else 0


def _insert_snapshot(cursor, jobs_inserted: int, total_jobs: int) -> None:
    """Records a summary of this pipeline run in the snapshots table."""
    sql = """
        INSERT INTO snapshots (pulled_at, jobs_inserted, total_jobs)
        VALUES (%s, %s, %s)
    """
    cursor.execute(sql, (datetime.now(), jobs_inserted, total_jobs))


if __name__ == "__main__":
    # Run the full ETL pipeline end-to-end when called directly
    from pipeline.extract import fetch_jobs
    from pipeline.transform import transform_jobs, parse_skills

    raw = fetch_jobs()
    jobs = transform_jobs(raw)
    skills = parse_skills(jobs)
    load(jobs, skills)
