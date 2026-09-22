# Clean Clone Verification Checklist

Use this checklist when verifying that the repository is fully reproducible
from a clean clone. Complete each item in order. Do not mark an item as done
until it is verified, not just attempted.

---

## Environment Setup

- [ ] Repository cloned into an empty directory
- [ ] Python 3.12+ virtual environment created (`.venv`)
- [ ] Dependencies installed from `requirements.txt`
- [ ] `.env` created from `.env.example`
- [ ] All required variables in `.env` are populated (not empty placeholders)

---

## Infrastructure

- [ ] `docker compose up -d` succeeds
- [ ] `docker compose ps` shows `postgres`, `qdrant`, and `redis` as healthy
- [ ] `alembic upgrade head` applies all migrations without error
- [ ] `alembic current` shows the expected revision hash

---

## Database Setup

- [ ] `python scripts/setup_readonly_role.py` succeeds
- [ ] `financial_reader` role can connect using `READONLY_DATABASE_URL`
- [ ] `financial_reader` role **cannot** write to `customers`, `accounts`, or `transactions`
- [ ] `approval_requests` and `audit_events` are **not** accessible to `financial_reader`

---

## Data Population

- [ ] `python scripts/seed_database.py` seeds data (or reports already seeded)
- [ ] Database contains at least one customer, account, and transaction
- [ ] Transaction `TX-1006` is present in the database

---

## Vector Store & Collections

- [ ] `python scripts/index_policies.py` completes without error
- [ ] `financial_policies` Qdrant collection contains indexed vectors
- [ ] `python scripts/setup_memory_store.py` completes without error
- [ ] `financial_memory` Qdrant collection exists

---

## Checkpoint Storage

- [ ] `python scripts/setup_checkpoints.py` succeeds
- [ ] LangGraph checkpoint tables exist in PostgreSQL

---

## Environment Verification

- [ ] `python scripts/verify_setup.py` exits 0 with all `[OK]` checks

---

## Test Suite

- [ ] `pytest tests/unit -v` passes (no infrastructure required)
- [ ] `pytest tests/security -v` passes
- [ ] `ruff check src tests scripts` passes with no errors

---

## API

- [ ] `uvicorn app.main:app --app-dir src` starts without error
- [ ] `GET /api/v1/health` returns `{"status": "ok"}`
- [ ] `GET /api/v1/ready` returns `{"status": "ready"}` (requires PostgreSQL + Qdrant)

---

## Investigation Workflow

- [ ] TX-1006 investigation completes successfully via the API
- [ ] Response includes structured evidence (SQL rows, risk score, policy citation)
- [ ] Same-thread follow-up (`thread_id: demo-001`) resolves pronoun references correctly
- [ ] Unsupported policy question (e.g. cryptocurrency withdrawals) is reported as ungrounded
- [ ] Chart artifact is generated from verified analytics values

---

## Security Workflow

- [ ] Attempt to execute a freeze without approval → `ActionNotAllowedError` + denial audit
- [ ] Attempt with wrong `account_id` argument → `ActionNotAllowedError` + `argument_mismatch` audit
- [ ] Approve and execute correct freeze → success + `action_executed` audit
- [ ] Attempt replay of the same approval → `ActionNotAllowedError` + `approval_already_executed` audit

---

## MCP

- [ ] MCP server starts and discovers intended tools (`health_check`, `assess_risk`, `query_financial_data`)
- [ ] Dangerous mutations (e.g. `freeze_account`) are **not** autonomously exposed through MCP
- [ ] `query_financial_data` routes through `SafeSQLTool` boundary

---

## Evaluation

- [ ] Golden evaluation dataset contains ≥ 20 representative cases
- [ ] Evaluation runner completes without LLM call errors

---

## Docker Build

- [ ] `docker build -t financial-intelligence-platform .` succeeds
- [ ] `docker compose up --build` starts the API container
- [ ] Containerised `GET /api/v1/health` returns `{"status": "ok"}`

---

## Sign-off

| Date | Engineer | Notes |
|---|---|---|
| | | |
