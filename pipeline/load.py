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

    # One timestamp for the whole run, to whole seconds, so the value stored in
    # jobs.last_seen exactly equals the value used to filter skill_snapshots.
    run_ts = datetime.now().replace(microsecond=0)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        jobs_inserted = _insert_jobs(cursor, jobs)
        skills_inserted = _insert_skills(cursor, skills)
        _bump_last_seen(cursor, jobs, run_ts)
        total_jobs = _get_total_jobs(cursor)
        snapshot_id = _insert_snapshot(cursor, run_ts, jobs_inserted, total_jobs)
        _insert_skill_snapshots(cursor, snapshot_id, run_ts)

        # Commit all inserts together — if anything above raised, we never reach here
        conn.commit()
        print(f"\nLoad complete.")
        print(f"  Jobs inserted this run : {jobs_inserted}")
        print(f"  Total jobs in DB       : {total_jobs}")
        print(f"  Skill records inserted : {skills_inserted}")

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


def _insert_skills(cursor, skills: list) -> int:
    """
    Inserts skill records linked to their job via job_id. INSERT IGNORE + the
    UNIQUE(job_id, skill_name) constraint de-duplicate within and across runs.
    Returns the count of rows actually inserted (duplicates are skipped).
    """
    sql = """
        INSERT IGNORE INTO skills (job_id, skill_name, frequency)
        VALUES (%(job_id)s, %(skill_name)s, %(frequency)s)
    """
    cursor.executemany(sql, skills)
    inserted = cursor.rowcount
    print(f"Skill records: {len(skills)} processed, {inserted} new")
    return inserted


def _get_total_jobs(cursor) -> int:
    """Queries the total number of rows in the jobs table after this run's inserts."""
    cursor.execute("SELECT COUNT(*) FROM jobs")
    result = cursor.fetchone()
    return result[0] if result else 0


def _insert_snapshot(cursor, run_ts, jobs_inserted: int, total_jobs: int) -> int:
    """
    Records a summary of this pipeline run in the snapshots table and returns the
    new snapshot_id. pulled_at uses the shared run_ts so it matches jobs.last_seen.
    """
    sql = """
        INSERT INTO snapshots (pulled_at, jobs_inserted, total_jobs)
        VALUES (%s, %s, %s)
    """
    cursor.execute(sql, (run_ts, jobs_inserted, total_jobs))
    return cursor.lastrowid


def _bump_last_seen(cursor, jobs: list, run_ts) -> None:
    """
    Marks every job seen in this run as active now (last_seen = run_ts). Newly
    inserted rows get last_seen here too — INSERT IGNORE leaves it NULL on insert.
    INSERT IGNORE and the jobs_inserted rowcount are left untouched.
    """
    ids = [job["id"] for job in jobs]
    if not ids:
        return
    placeholders = ", ".join(["%s"] * len(ids))
    sql = f"UPDATE jobs SET last_seen = %s WHERE id IN ({placeholders})"
    cursor.execute(sql, [run_ts, *ids])


def _insert_skill_snapshots(cursor, snapshot_id: int, run_ts) -> None:
    """
    Appends one row per skill for this snapshot: how many DISTINCT jobs active this
    run (last_seen = run_ts) mention the skill, plus their avg max salary. The inner
    DISTINCT is redundant now skills is unique on (job_id, skill_name) — kept as a guard.
    """
    sql = """
        INSERT INTO skill_snapshots (snapshot_id, skill_name, job_count, avg_salary_max)
        SELECT %s, t.skill_name,
               COUNT(*) AS job_count,
               ROUND(AVG(NULLIF(t.salary_max, 0))) AS avg_salary_max
        FROM (
            SELECT DISTINCT s.job_id, s.skill_name, j.salary_max
            FROM skills s
            JOIN jobs j ON s.job_id = j.id
            WHERE j.last_seen = %s
        ) t
        GROUP BY t.skill_name
    """
    cursor.execute(sql, (snapshot_id, run_ts))


if __name__ == "__main__":
    # Run the full ETL pipeline end-to-end when called directly
    from pipeline.extract import fetch_jobs
    from pipeline.transform import transform_jobs, parse_skills

    raw = fetch_jobs()
    jobs = transform_jobs(raw)
    skills = parse_skills(jobs)
    load(jobs, skills)
