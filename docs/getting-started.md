# Getting Started

This guide walks you through setting up the Financial Intelligence & Risk
Platform from a clean clone. Follow the steps in order.

---

## Requirements

| Tool | Minimum Version |
|---|---|
| Python | 3.12 |
| Docker | 24+ |
| Docker Compose | v2 (bundled with Docker Desktop) |
| Git | any recent |

---

## 1. Clone the Repository

```bash
git clone https://github.com/zainexperience2005/financial-intelligence-risk-platform.git
cd financial-intelligence-risk-platform
```

---

## 2. Create a Virtual Environment

**Windows:**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in the required values:

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | Password for the `financial_app` database user |
| `DATABASE_URL` | Full connection URL for the write-capable app user |
| `READONLY_DATABASE_URL` | Connection URL for the read-only `financial_reader` user |
| `CHECKPOINT_DATABASE_URL` | Connection URL for LangGraph checkpoint storage (same DB, plain `postgresql://` scheme) |
| `OPENAI_API_KEY` | Your OpenAI API key (`sk-...`) |
| `LANGSMITH_API_KEY` | LangSmith tracing key (optional but recommended) |

> [!IMPORTANT]
> Never commit `.env` to version control. It is listed in `.gitignore`.

> [!NOTE]
> **Why three database URLs?**
> - `DATABASE_URL` — used by the application for all writes and trusted reads.
> - `READONLY_DATABASE_URL` — used exclusively by `SafeSQLTool` for model-generated queries. This role has only `SELECT` on `customers`, `accounts`, `transactions` and cannot touch `approval_requests` or `audit_events`.
> - `CHECKPOINT_DATABASE_URL` — used by LangGraph's `PostgresSaver` for conversation state. Uses the plain `postgresql://` scheme required by `psycopg`.

---

## 5. Start Local Infrastructure

```bash
docker compose up -d
```

Verify all services are healthy:

```bash
docker compose ps
```

Expected services:

| Service | Port | Notes |
|---|---|---|
| `postgres` | 5432 | PostgreSQL 16 |
| `qdrant` | 6333 | Vector store |
| `redis` | 6379 | Provisioned for future use; not required by core investigation workflow |

> [!NOTE]
> Redis is included in the Compose stack for future capability but is not currently required by the investigation, approval, or audit workflows. A healthy Redis is not a prerequisite for the API readiness check.

---

## 6. Apply Database Migrations

```bash
alembic upgrade head
```

Verify:

```bash
alembic current
```

This creates tables: `customers`, `accounts`, `transactions`, `approval_requests`, `audit_events`, `alembic_version`.

---

## 7. Configure the Read-Only Database Role

The `financial_reader` role is created automatically by Docker's init script (`infra/docker/postgres/init/01-roles.sql`). However, `GRANT SELECT` on tables must be issued after migrations create them:

```bash
python scripts/setup_readonly_role.py
```

This grants `SELECT` on `customers`, `accounts`, `transactions` to `financial_reader`. `approval_requests` and `audit_events` are intentionally excluded.

---

## 8. Seed Synthetic Demo Data

```bash
python scripts/seed_database.py
```

This is idempotent — it checks for existing data and skips if already seeded. Creates 3 customers, 3 accounts, and 6 transactions including the canonical demo transaction `TX-1006`.

---

## 9. Index Policy Documents

```bash
python scripts/index_policies.py
```

Indexes the financial policy documents from `data/policies/` into the `financial_policies` Qdrant collection. Policy documents include FIN-POL-001 (AML), FIN-POL-002 (KYC), and FIN-POL-003 (cross-border transfers).

---

## 10. Set Up the Memory Collection

```bash
python scripts/setup_memory_store.py
```

Creates the `financial_memory` Qdrant collection for long-term investigation memory. Skipped automatically if the collection already exists.

---

## 11. Initialise LangGraph Checkpoints

```bash
python scripts/setup_checkpoints.py
```

Creates the LangGraph checkpoint tables (`checkpoints`, `checkpoint_writes`, `checkpoint_blobs`) in PostgreSQL. Idempotent — safe to run multiple times.

---

## 12. Verify the Environment

Run the environment verification script to confirm everything is ready:

```bash
python scripts/verify_setup.py
```

Expected output:

```text
[OK] PostgreSQL (write connection)
[OK] Database migrations (revision: <hash>)
[OK] Financial schema (all tables present)
[OK] Synthetic data (3 customers, 3 accounts, 6 transactions)
[OK] Read-only database role (financial_reader)
[OK] Qdrant
[OK] Policy collection 'financial_policies' (<N> vectors)
[OK] Memory collection 'financial_memory'
[OK] LangGraph checkpoints (3 tables present)
[OK] LLM configuration (OPENAI_API_KEY present)

Environment verification passed. All 10 checks succeeded.
```

Fix any `[FAIL]` items before proceeding.

---

## 13. Run Tests

```bash
# Unit tests (no external dependencies)
pytest tests/unit -v

# Security tests (uses local SQLite test database)
pytest tests/security -v

# Integration tests (requires running infrastructure)
pytest tests/integration -v

# Code quality
ruff check src tests scripts
```

---

## 14. Start the API

```bash
uvicorn app.main:app --app-dir src --reload
```

Or using Make:

```bash
make up     # start with Docker Compose
make logs   # tail API logs
```

Verify liveness:

```bash
curl http://localhost:8000/api/v1/health
# {"status": "ok"}
```

Verify readiness (requires PostgreSQL + Qdrant):

```bash
curl http://localhost:8000/api/v1/ready
# {"status": "ready", "database": "ok", "dependencies": {...}}
```

---

## 15. First Investigation

Investigate the canonical demo transaction:

```bash
curl -X POST http://localhost:8000/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{"question": "Investigate TX-1006 and explain its risk.", "thread_id": "demo-001"}'
```

The workflow executes:

```
Planner → SQL Analyst → Risk Engine → Report Synthesis
```

The response includes a structured `InvestigationReport` with SQL evidence, a deterministic risk score, applicable policy citations, and a narrative summary.

---

## Alternative: Run All Bootstrap Steps at Once

```bash
python scripts/bootstrap.py
```

Then run the data-population steps manually:

```bash
python scripts/setup_readonly_role.py
python scripts/seed_database.py
python scripts/index_policies.py
python scripts/verify_setup.py
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` | Running script without `.venv` active | Activate `.venv` first |
| `connection refused` on port 5432 | PostgreSQL not running | `docker compose up -d postgres` |
| `[FAIL] Read-only database role` | GRANT not issued | `python scripts/setup_readonly_role.py` |
| `[FAIL] Policy collection` | Qdrant empty | `python scripts/index_policies.py` |
| `[FAIL] LLM configuration` | Missing API key | Set `OPENAI_API_KEY` in `.env` |
| `alembic upgrade head` fails | DB unreachable or wrong URL | Check `DATABASE_URL` in `.env` |
