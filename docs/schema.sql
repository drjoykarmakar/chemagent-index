BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> f03fd98cb26f

CREATE TABLE audit_logs (
    id VARCHAR(80) NOT NULL, 
    created_at VARCHAR(40) NOT NULL, 
    event VARCHAR(80) NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE benchmarks (
    id VARCHAR(80) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE leaderboard_snapshots (
    id VARCHAR(80) NOT NULL, 
    created_at VARCHAR(40) NOT NULL, 
    cohort VARCHAR(64) NOT NULL, 
    fingerprint VARCHAR(64) NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE models (
    id VARCHAR(80) NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE organizations (
    id VARCHAR(80) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE submissions (
    id VARCHAR(80) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    created_at VARCHAR(40) NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE agents (
    id VARCHAR(80) NOT NULL, 
    base_model_id VARCHAR(80), 
    data JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(base_model_id) REFERENCES models (id)
);

CREATE TABLE benchmark_versions (
    id VARCHAR(100) NOT NULL, 
    benchmark_id VARCHAR(80) NOT NULL, 
    version VARCHAR(30) NOT NULL, 
    fingerprint VARCHAR(64) NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(benchmark_id) REFERENCES benchmarks (id), 
    UNIQUE (fingerprint)
);

CREATE TABLE users (
    id VARCHAR(80) NOT NULL, 
    organization_id VARCHAR(80), 
    role VARCHAR(30) NOT NULL, 
    external_subject VARCHAR(200) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    UNIQUE (external_subject)
);

CREATE TABLE api_keys (
    id VARCHAR(80) NOT NULL, 
    user_id VARCHAR(80) NOT NULL, 
    key_hash VARCHAR(128) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE benchmark_tasks (
    id VARCHAR(160) NOT NULL, 
    version_id VARCHAR(100) NOT NULL, 
    task_id VARCHAR(100) NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(version_id) REFERENCES benchmark_versions (id), 
    UNIQUE (version_id, task_id)
);

CREATE TABLE evaluations (
    id VARCHAR(80) NOT NULL, 
    model_id VARCHAR(80) NOT NULL, 
    version_id VARCHAR(100) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(model_id) REFERENCES models (id), 
    FOREIGN KEY(version_id) REFERENCES benchmark_versions (id)
);

CREATE TABLE evaluation_runs (
    id VARCHAR(80) NOT NULL, 
    evaluation_id VARCHAR(80) NOT NULL, 
    model_id VARCHAR(80) NOT NULL, 
    version_id VARCHAR(100) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    cohort VARCHAR(64) NOT NULL, 
    identity VARCHAR(64) NOT NULL, 
    created_at VARCHAR(40) NOT NULL, 
    completed_at VARCHAR(40), 
    provenance JSON NOT NULL, 
    summary JSON, 
    PRIMARY KEY (id), 
    FOREIGN KEY(evaluation_id) REFERENCES evaluations (id), 
    FOREIGN KEY(model_id) REFERENCES models (id), 
    FOREIGN KEY(version_id) REFERENCES benchmark_versions (id)
);

CREATE INDEX ix_evaluation_runs_cohort ON evaluation_runs (cohort);

CREATE INDEX ix_evaluation_runs_model_id ON evaluation_runs (model_id);

CREATE TABLE responses (
    id VARCHAR(80) NOT NULL, 
    run_id VARCHAR(80) NOT NULL, 
    task_id VARCHAR(100) NOT NULL, 
    raw VARCHAR NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(run_id) REFERENCES evaluation_runs (id), 
    UNIQUE (run_id, task_id)
);

CREATE INDEX ix_responses_run_id ON responses (run_id);

CREATE TABLE citations (
    id VARCHAR(80) NOT NULL, 
    response_id VARCHAR(80) NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(response_id) REFERENCES responses (id)
);

CREATE TABLE scores (
    id VARCHAR(80) NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES responses (id)
);

CREATE TABLE validation_results (
    id VARCHAR(80) NOT NULL, 
    data JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES responses (id)
);

INSERT INTO alembic_version (version_num) VALUES ('f03fd98cb26f') RETURNING alembic_version.version_num;

COMMIT;

