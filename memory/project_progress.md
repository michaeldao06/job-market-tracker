---
name: project-progress
description: Build status of job-market-tracker ETL pipeline
metadata:
  type: project
---

**Completed as of 2026-05-12:**
- `db/schema.sql` — created and committed. Includes `CREATE DATABASE IF NOT EXISTS job_market_tracker` + 3 tables: `jobs`, `skills`, `snapshots`. Schema also uses `USE job_market_tracker`.

**Up next (not started):**
- `pipeline/extract.py` — Adzuna API pulls
- `pipeline/transform.py` — pandas cleaning
- `pipeline/load.py` — MySQL inserts
- `api/main.py` — FastAPI endpoints

**Why:** Portfolio ETL project. Schema-first approach per CLAUDE.md.
**How to apply:** Always check `db/schema.sql` before writing any queries or inserts.
