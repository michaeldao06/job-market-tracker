-- 001_skill_timeseries.sql
--
-- One-time migration for the skill demand time-series feature, for an EXISTING
-- database that already holds data (a fresh DB is covered by db/schema.sql).
--
-- Safe to re-run: column/index adds are guarded via information_schema and the
-- table uses IF NOT EXISTS, so a second apply -- or a re-run after a partial
-- failure -- skips what's already done and completes the rest. (MySQL has no
-- ADD COLUMN/KEY IF NOT EXISTS, unlike MariaDB, hence the guards.)
--
-- Atomicity -- a real MySQL limitation, stated plainly:
--   * ALTER TABLE and CREATE TABLE are DDL and cause an IMPLICIT COMMIT in MySQL.
--     They cannot be rolled back by wrapping them in a transaction, and multiple
--     DDL statements cannot be made atomic as a group in plain SQL.
--   * Only the data-only steps (the last_seen backfill UPDATE and the dedupe
--     DELETE) are transactional. They run inside one START TRANSACTION / COMMIT,
--     and each is idempotent on its own.
--   * Recovery from a partial failure is therefore "re-run this file", not a
--     rollback -- the guards make re-running converge to the correct end state.
--     True all-or-nothing across the DDL would require a DB with transactional
--     DDL (e.g. PostgreSQL) or a migration tool that tracks applied state and
--     fixes forward (Flyway / Liquibase / Alembic).
--
-- Run order: safe-updates off -> add last_seen (DDL) -> [txn: backfill + dedupe]
--            -> add unique key (DDL) -> create skill_snapshots (DDL) -> restore.

USE job_market_tracker;

-- Workbench defaults SQL_SAFE_UPDATES = 1, which blocks the dedupe DELETE
-- (error 1175). Turn it off for this session so the file is self-contained,
-- and restore the previous value at the end.
SET @old_safe_updates := @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;

-- 1. jobs.last_seen  (DDL -- implicit commit, cannot be rolled back) ----------
SET @add_last_seen := (
    SELECT COUNT(*) = 0
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'jobs'
      AND COLUMN_NAME  = 'last_seen'
);
SET @sql := IF(@add_last_seen,
    'ALTER TABLE jobs ADD COLUMN last_seen DATETIME NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2. Data-only steps, grouped in one transaction ------------------------------
--    last_seen must exist (step 1) before the backfill; the dedupe must precede
--    the unique key (step 3). Both statements are also individually idempotent.
START TRANSACTION;

    -- Backfill last_seen for rows that predate the column (only NULLs).
    UPDATE jobs SET last_seen = date_pulled WHERE last_seen IS NULL;

    -- Collapse duplicate (job_id, skill_name) rows, keeping the lowest skill_id.
    DELETE s1 FROM skills s1
    JOIN skills s2
      ON s1.job_id     = s2.job_id
     AND s1.skill_name = s2.skill_name
     AND s1.skill_id   > s2.skill_id;

COMMIT;

-- 3. skills unique key  (DDL -- implicit commit) ------------------------------
SET @add_uq := (
    SELECT COUNT(*) = 0
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'skills'
      AND INDEX_NAME   = 'uq_job_skill'
);
SET @sql := IF(@add_uq,
    'ALTER TABLE skills ADD UNIQUE KEY uq_job_skill (job_id, skill_name)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4. skill_snapshots  (DDL -- implicit commit) --------------------------------
CREATE TABLE IF NOT EXISTS skill_snapshots (
    snapshot_id    INT          NOT NULL,
    skill_name     VARCHAR(100) NOT NULL,
    job_count      INT          NOT NULL,
    avg_salary_max INT          NULL,
    PRIMARY KEY (snapshot_id, skill_name),
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

-- Restore the session's previous safe-update setting.
SET SQL_SAFE_UPDATES = @old_safe_updates;
