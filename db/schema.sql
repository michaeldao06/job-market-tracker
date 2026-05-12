CREATE DATABASE IF NOT EXISTS job_market_tracker;
USE job_market_tracker;

REATE TABLE IF NOT EXISTS jobs (
    id               VARCHAR(20)  PRIMARY KEY,
    title            VARCHAR(255) NOT NULL,
    company          VARCHAR(255) NOT NULL,
    location         VARCHAR(255) NOT NULL,
    salary_min       INT          NULL,
    salary_max       INT          NULL,
    salary_is_predicted TINYINT(1) NOT NULL DEFAULT 0,
    contract_type    VARCHAR(50)  NULL,
    contract_time    VARCHAR(50)  NULL,
    category         VARCHAR(255) NOT NULL,
    description      TEXT         NULL,
    date_posted      DATETIME     NOT NULL,
    date_pulled      DATETIME     NOT NULL
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id   INT AUTO_INCREMENT PRIMARY KEY,
    job_id     VARCHAR(20)  NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    frequency  INT          NOT NULL DEFAULT 1,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id INT AUTO_INCREMENT PRIMARY KEY,
    pulled_at   DATETIME NOT NULL,
    job_count   INT      NOT NULL
);
