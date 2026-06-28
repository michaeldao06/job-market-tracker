import os
from typing import Optional

import mysql.connector
from mysql.connector import Error
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Job Market Tracker API")

# Allow the browser (Live Server or any local origin) to call the API.
# Without this, browsers block cross-origin fetch requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_connection():
    """Opens and returns a fresh MySQL connection using credentials from .env."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/")
def serve_dashboard():
    """Serves the frontend dashboard so the whole app runs from one server."""
    path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    return FileResponse(path)


# ── /skills/trending ──────────────────────────────────────────────────────────

@app.get("/skills/trending")
def skills_trending(limit: int = Query(default=10, ge=1, description="Number of top skills to return")):
    """
    Returns the top N skills ranked by total frequency across all job postings.
    Useful for seeing what skills are most in-demand right now.
    """
    sql = """
        SELECT skill_name, SUM(frequency) AS total_frequency
        FROM skills
        GROUP BY skill_name
        ORDER BY total_frequency DESC
        LIMIT %s
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        # dictionary=True makes each row a dict instead of a plain tuple
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        return rows

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# ── /jobs/search ──────────────────────────────────────────────────────────────

@app.get("/jobs/search")
def jobs_search(skill: str = Query(..., description="Skill name to search for (case-insensitive)")):
    """
    Returns jobs that have a matching skill record.
    JOIN pulls only jobs where the given skill appears in the skills table.
    """
    sql = """
        SELECT DISTINCT j.id, j.title, j.company, j.location, j.category, j.date_posted
        FROM jobs j
        JOIN skills s ON j.id = s.job_id
        WHERE LOWER(s.skill_name) = LOWER(%s)
        ORDER BY j.date_posted DESC
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (skill,))
        rows = cursor.fetchall()

        # Convert datetime objects to strings so FastAPI can serialise them to JSON
        for row in rows:
            if row.get("date_posted"):
                row["date_posted"] = str(row["date_posted"])

        return rows

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# ── /salaries/by-role ─────────────────────────────────────────────────────────

@app.get("/salaries/by-role")
def salaries_by_role():
    """
    Returns average salary range per job title, ordered by avg_salary_max descending.
    Excludes jobs where salary data is missing or zero to keep averages meaningful.
    """
    sql = """
        SELECT
            title,
            ROUND(AVG(salary_min)) AS avg_salary_min,
            ROUND(AVG(salary_max)) AS avg_salary_max,
            COUNT(*) AS job_count
        FROM jobs
        WHERE salary_min > 0 AND salary_max > 0
        GROUP BY title
        ORDER BY avg_salary_max DESC
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        rows = cursor.fetchall()
        return rows

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# ── /skills/valuable ──────────────────────────────────────────────────────────

@app.get("/skills/valuable")
def skills_valuable(limit: int = Query(default=10, ge=1, description="Number of top skills to return")):
    """
    Returns the most valuable skills ranked by the average max salary of jobs they appear in.
    Only considers jobs with actual salary data (salary_min > 0 AND salary_max > 0).
    """
    sql = """
        SELECT
            s.skill_name,
            ROUND(AVG(j.salary_max)) AS avg_salary_max,
            COUNT(*) AS job_count
        FROM skills s
        JOIN jobs j ON s.job_id = j.id
        WHERE j.salary_min > 0 AND j.salary_max > 0
        GROUP BY s.skill_name
        HAVING job_count >= 10
        ORDER BY avg_salary_max DESC
        LIMIT %s
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        return rows

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# ── /skills/timeseries ────────────────────────────────────────────────────────

@app.get("/skills/timeseries")
def skills_timeseries(skill: str = Query(..., description="Skill name to chart over time (case-insensitive)")):
    """
    Returns the per-run active job count (and avg max salary) for a skill over time,
    one point per snapshot. LEFT JOIN so a run where the skill had zero active jobs
    shows as 0 instead of dropping out; scoped to snapshots that actually have skill
    data so pre-feature runs don't appear as fake zeros.
    """
    sql = """
        SELECT sn.pulled_at,
               COALESCE(ss.job_count, 0) AS job_count,
               ss.avg_salary_max
        FROM snapshots sn
        JOIN (SELECT DISTINCT snapshot_id FROM skill_snapshots) have
          ON have.snapshot_id = sn.snapshot_id
        LEFT JOIN skill_snapshots ss
          ON ss.snapshot_id = sn.snapshot_id
         AND LOWER(ss.skill_name) = LOWER(%s)
        ORDER BY sn.pulled_at ASC
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (skill,))
        rows = cursor.fetchall()

        # Convert datetime objects to strings so FastAPI can serialise them to JSON
        for row in rows:
            if row.get("pulled_at"):
                row["pulled_at"] = str(row["pulled_at"])

        return rows

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
