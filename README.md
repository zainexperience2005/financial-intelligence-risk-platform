# Financial Intelligence & Risk Platform

[![CI](https://github.com/zainexperience2005/financial-intelligence-risk-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/zainexperience2005/financial-intelligence-risk-platform/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-dc2626.svg)](https://qdrant.tech/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-161%20passed-brightgreen.svg)](#-testing--verification)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](./Dockerfile)

An enterprise-grade, production-oriented **Agentic AI platform for financial intelligence, fraud investigation, and controlled risk mitigation**.

The platform integrates **LangGraph multi-agent orchestration**, **PostgreSQL**, **Qdrant**, **AST-validated SafeSQL**, **Corrective RAG (CRAG)**, a **deterministic risk engine**, and a **tamper-evident human-in-the-loop approval & audit workflow** with real, controlled database mutations — all exposed through a production-structured **FastAPI** backend.

---

## 🏛️ Architectural Overview

The repository strictly enforces a clean architectural separation between domain-independent agentic infrastructure and domain-specific financial intelligence:

```
src/
├── kit/       # Reusable Agentic AI Infrastructure (Domain-Independent)
└── app/       # Financial Intelligence & Risk Platform (Domain-Specific)
```

### Dependency Rules & Design Principles
- **Unidirectional Dependency**: `app` depends on `kit`. `kit` **never** imports from `app`.
- **Infrastructure Reusability**: LLM factories, SQL AST validators, vector store clients, RAG/CRAG pipelines, generic tool registries, and loop controls live in `kit`.
- **Domain Confinement**: Financial prompts, database models (accounts, transactions, approvals, audit events), policy ingestion, risk rules, and business workflows live strictly in `app`.
- **Deterministic Routing**: Workflow routing uses structured state variables and Python conditions — never redundant LLM router calls.
- **Authoritative Evidence Separation**: Specialist agents retrieve and compute authoritative facts. The report agent explains verified evidence without recalculating or inventing numbers.
- **Strict Trust Boundary**: Models may recommend actions, but **never** hold direct database write access or bypass human review.

---

## 🔄 Multi-Agent Investigation Topology

The platform coordinates specialized autonomous agents in a compiled **LangGraph** state graph:

```mermaid
flowchart TD
    START([START]) --> PrepareTurn[Prepare Turn\nprepare_turn\nResets Turn-Scoped Evidence]
    PrepareTurn --> Planner[Planner Agent\nplan_investigation\n+ Bounded Conversation Context]

    Planner -->|requires_sql = true| SQL[SQL Analyst Agent\nanalyze_sql]
    Planner -->|requires_policy only| PolicyAgent[Policy Agent\nCRAG / analyze_policy]
    Planner -->|direct inquiry| Analyze[Financial Assistant\nanalyze_question]

    SQL -->|requires_analytics| DataAnalyst[Data Analyst Agent\nanalyze_data]
    SQL -->|requires_policy| PolicyAgent
    SQL -->|requires_risk| RiskCheck{Single row?}
    SQL -->|no further work| Report

    DataAnalyst -->|requires_policy| PolicyAgent
    DataAnalyst -->|requires_risk| RiskCheck
    DataAnalyst -->|done| Report

    PolicyAgent --> RiskCheck

    RiskCheck -->|yes - 1 row| RiskAgent[Deterministic Risk Engine\n+ Risk Explanation Agent]
    RiskCheck -->|no - multi-row or none| Report[Report Synthesis Agent\nInvestigationReport]

    RiskAgent --> Report
    Report --> END_NODE([END])
    Analyze --> END_NODE
```

### Agents & Specialist Roles

| Agent / Node | Primary Responsibility | Guardrails & Safety Controls |
|---|---|---|
| **Planner Agent** | Analyzes inquiries; generates a typed `InvestigationPlan` with capability flags. | Structured Pydantic output; no DB access. |
| **SQL Analyst Agent** | Retrieves authoritative financial records. | AST single-statement validation (`sqlglot`), SELECT-only enforcement, iteration budgets. |
| **Data Analyst Agent** | Computes aggregations, sums, counts, variance over retrieved rows. | Pure deterministic Python/Pandas; bounded tool-call limits. |
| **Policy Agent** | Grounds findings in compliance policy docs using **Corrective RAG (CRAG)**. | Evaluates chunk relevance; bounded corrective retrieval; explicit refusal when unanswerable. |
| **Risk Agent** | Evaluates deterministic risk signals against transaction evidence. | Scores computed by deterministic engine — never fabricated by the LLM. |
| **Report Agent** | Synthesizes specialist findings into an analyst-ready `InvestigationReport`. | Derives findings solely from authoritative evidence; cannot execute mutations. |

---

## 🛡️ Controlled Actions, Human Approvals & Persistent Audit Trail

One of the platform's core achievements is crossing from passive investigation into **real, controlled customer-impacting database mutations** while maintaining an absolute trust boundary:

```text
                  AI Reasoning & Investigation
                               │
                               ▼
                    Action Recommendation
                               │
              ─────────────────┴─────────────────
                         TRUST BOUNDARY
                               │
                               ▼
                    Action Proposal Created
                               │
                               ▼
                     Human Compliance Review
                         /          \
                    reject          approve
                      │                │
                     STOP              ▼
                             Exact Action Check
                                       │
                             Exact Arguments Check
                                       │
                              Single-Use Verification
                                       │
                                       ▼
                             Controlled Repository
                                       │
                                       ▼
                            PostgreSQL Transaction
                                       │
                     ┌─────────────────┼─────────────────┐
                     ▼                 ▼                 ▼
             account.status =     approval.status =   audit_events
                 'frozen'            'executed'         recorded
```

### Key Security & Integrity Guarantees

1. **Dual-Database Role Separation**:
   - `financial_reader`: SELECT-only PostgreSQL user for `SafeSQLTool`. Never sees `approval_requests` or `audit_events`.
   - `financial_user`: Application credentials used by deterministic repositories only. Never exposed to models.

2. **Deterministic Pre-Execution Verification**:
   - Approval exists and `status == "approved"`.
   - Action name matches exactly (`freeze_account`).
   - Arguments match exactly (`account_id` target).
   - Single-use: replays and already-executed approvals are rejected.
   - Row-level locking (`SELECT FOR UPDATE`) prevents concurrent double-execution.

3. **Atomic Single-Transaction Execution**:
   ```python
   try:
       freeze_account_record(account)
       mark_approval_executed(approval)
       record_audit_event(session, ...)
       session.commit()
   except Exception:
       session.rollback()
       _record_denied_attempt(...)  # isolated audit in a separate transaction
       raise
   ```

4. **Tamper-Evident Audit Trail**: Every state change (`approval_requested`, `approval_approved`, `approval_rejected`, `action_executed`, `action_execution_denied`) is permanently recorded with timestamp, actor, entity ID, and context metadata.

---

## 🧮 Deterministic Risk Engine

The risk score is always computed by deterministic Python — **never by an LLM**:

| Signal | Trigger Condition | Points |
|---|---|---|
| `HIGH_VALUE` | Amount ≥ PKR 400,000 | +30 |
| `HIGH_VALUE_INTERNATIONAL` | International transfer ≥ PKR 300,000 | +25 |
| `FAILED_TRANSACTION` | `status == "failed"` | +10 |
| `RISK_REVIEW_FAILURE` | `failure_reason == "risk_review"` | +25 |

Scores are capped at 100. Risk levels: `low` (< 40), `medium` (40–69), `high` (≥ 70).

### Evidence Sufficiency (Step 31.1 — Semantic Fix)

`evidence_sufficient` reflects whether the risk agent had the required authoritative inputs to produce a valid risk score:

```python
# ✅ Correct — sufficient when we have the transaction row + deterministic assessment
evidence_sufficient = bool(transaction and assessment)

# ✅ Separate quality signal — policy retrieval quality is tracked independently
policy_grounded = bool(policy_analysis and policy_analysis.grounded)
```

Previously, `evidence_sufficient` was wrongly tied to `policy_grounded`, which would mark a fully-resolved high-risk transaction as "insufficient" simply because policy retrieval wasn't run.

### Multi-Transaction Guard (Step 31.2)

Risk analysis requires **a single unambiguous transaction**. When a query returns multiple rows (e.g., "show me all transactions for ACC-1001"), the risk node skips scoring and lets the report note the limitation:

```python
if len(sql_analysis.rows) > 1:
    return {}  # Skip — scope is ambiguous; report agent will note this
```

---

## 🧠 Persistent Short-Term Memory with LangGraph Checkpointing

The platform persists conversation context across turns via **PostgreSQL checkpointing (`PostgresSaver`)**:

```text
Turn 1: "Investigate TX-1006."
  └─► Planner retrieves TX-1006 records, evaluates risk, synthesizes report
  └─► Executive summary saved to conversation thread (AIMessage)

Turn 2: "Why was it considered high risk?" (same thread_id)
  └─► prepare_turn resets stale specialist evidence (SQL, analytics, policy, report)
  └─► Planner receives bounded recent conversation window (last 6 messages)
  └─► Planner resolves "it" -> "TX-1006" and orchestrates targeted verification
```

**Rules:**
1. `thread_id` identifies an investigation thread, not a user.
2. Turn-scoped specialist state (`plan`, `sql_analysis`, `risk_analysis`, `report`) is reset by `prepare_turn` at the start of every turn.
3. `messages` accumulates across turns via the `add_messages` reducer.
4. `format_recent_context()` bounds context to the last 6 messages — preventing token bloat.

---

## 💾 Durable Long-Term Memory with Qdrant

| Capability | Storage | Semantics | Lifecycle |
|---|---|---|---|
| **Short-Term Memory** | PostgreSQL Checkpointer | Turn-to-turn dialogue (`thread_id`) | Active investigation thread |
| **Long-Term Memory** | Qdrant (`financial_memory`) | Selective historical findings | Explicit retention + deletion |
| **Policy RAG / CRAG** | Qdrant (`financial_policies`) | Authoritative compliance rules | Version-controlled documents |
| **Transactional Facts** | PostgreSQL (Relational) | Authoritative ground truth | ACID, audited |

**Principles:** selective persistence, explicit expiration, stable `memory_id` for deletion, no credentials or unnecessary PII.

---

## 📚 Corrective RAG (CRAG) Architecture

Standard vector retrieval can match keywords while missing the actual policy question. CRAG adds evaluation and correction:

```text
                    User Policy Inquiry
                             │
                             ▼
                  Vector Retrieval (Qdrant)
                             │
                             ▼
                  LLM Evidence Evaluator
                             │
              ┌──────────────┴──────────────┐
              │                             │
           Relevant                  Weak / Irrelevant
              │                             │
              │                             ▼
              │                       Query Rewriter
              │                             │
              │                      Vector Retrieval
              │                             │
              │                      Re-evaluation
              │                     ┌───────┴───────┐
              │                     │               │
              │                  Usable        Insufficient
              └──────────────┬──────┘               │
                             ▼                      ▼
                       Policy Evidence      Explicit Refusal
```

- **Relevance Grading**: `relevant`, `partial`, or `irrelevant`.
- **Bounded Correction**: One corrective retrieval attempt with a rewritten query.
- **Answerability Guard**: Explicit refusal rather than fabricated thresholds.

---

## ⚙️ Loop Engineering & Reusable Agent Runtime (Steps 32–36)

To move beyond unconstrained `while True:` agent loops, the platform includes a modular, domain-independent **Loop Engineering and Agent Control Stack** inside `src/kit/`:

```text
                    USER / SYSTEM
                         │
                         ▼
                  Context Builder
           (Priority-based budget degradation)
                         │
              Bounded Context Window
                         │
                         ▼
                    ReAct Agent
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
      Loop Controller             LLM Usage
     (Restorable state)      (Tokens + Cost USD)
      │   │   │   │                   │
  iters tools fails reps              │
      │   │   │   │                   ▼
      └───┴───┴───┴─────────── Fail-Closed Check
                  │
             Loop Guard
                  │
        (Pre-execution check)
                  │
                  ▼
       Controlled Tool Executor
         (Bounded Exponential Retries)
           ↙                     ↘
      Success             Permanent Failure
         │                         │
         ▼                         ▼
    Observation           controller.record_failure()
         │                         │
         └───────────┬─────────────┘
                     ▼
             Continue or Halt?
              ↙             ↘
          Allow             END
```

### 1. Reusable Loop Controller (`kit/loops`)
- **Restorable State**: Stored as serializable Pydantic models (`LoopBudget`, `LoopStatus`, `LoopUsage`), avoiding active runtime objects inside LangGraph/PostgreSQL checkpoints.
- **Multi-Dimensional Budgets**: Enforces iterations, tool calls, failures, repeated action signatures, token consumption, and cost in USD.
- **Action Signature Deduplication**: Computes canonical SHA-256 signatures of tool calls (`tool_name` + sorted arguments) to stop repeated actions before execution.

### 2. Controlled Tool Executor & Retry Policies (`kit/tools`)
- **Transient vs. Permanent Classification**: Retries timeouts, connection resets, and HTTP 502/503/429 with bounded exponential backoff (`RetryPolicy`), while validation errors, syntax errors, and permission denials halt immediately without retries.
- **Accounting Separation**: Internal retry attempts are not counted as separate agent iterations; a tool failure is recorded only when the controlled executor exhausts all attempts.
- **Exception Sanitization**: Unhandled exceptions are masked as generic `INTERNAL_TOOL_ERROR` observations to prevent leaking database connection strings or filesystem paths to the LLM.

### 3. Model Usage Tracking & Decoupled Pricing (`kit/llms`)
- **Usage Extraction**: Extracts input, output, and cache-read tokens directly from provider response metadata.
- **Decoupled Pricing Registry**: `PricingRegistry` maps model IDs to rate configurations (`ModelPricing`) without hardcoding rates in agent prompts or business logic.
- **Fail-Closed Cost Safeguard**: If a cost budget ceiling is configured but the model response cannot be priced, execution fails closed with `StopReason.UNKNOWN_COST`.
- **Tool Suppression**: If an LLM call exhausts a token or cost budget while proposing tool calls, routing halts immediately at `END` — the proposed tools are never executed.

### 4. Context & Memory Budget Engineering (`kit/context`, `app/services/sql_context`)
- **Typed Context Categories**: `SYSTEM`, `CURRENT_REQUEST`, `CONVERSATION`, `TOOL_RESULT`, `RETRIEVAL`, `MEMORY`.
- **Priority-Based Selection**: Fills available headroom with highest-priority items first and drops lower-priority items when capacity is reached.
- **Fail-Loud Required Context**: If essential system instructions or user requests exceed capacity, raises `ContextBudgetExceededError` (`StopReason.CONTEXT_BUDGET`) rather than silently discarding required facts.
- **SQL Context Bounding**: Slices raw SQL results to `MAX_MODEL_SQL_ROWS = 50` with explicit truncation metadata for model visibility, while deterministic analytics process the un-truncated dataset.

---

## 🎯 Formal Evaluation Foundation (Step 37)

To ensure the AI system performs reliably against known ground truth, the platform features a formal, repeatable evaluation suite:

```text
Golden Dataset (evals/datasets/financial_golden.json)
                         │
                         ▼
             Component / Workflow Runner
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
Deterministic Scorers  Grounding Scorers  Safety Invariants
 (exact/numeric match)   (source recall)   (hard gates)
         │               │               │
         └───────────────┼───────────────┘
                         ▼
        Evaluation Report (evals/reports/)
```

### Golden Dataset Coverage (24 Cases)
- **SQL Investigation (5)**: Single-row lookup, status filtering, customer history, threshold search, conversational bypass.
- **Deterministic Analytics (4)**: Account summarization, grouped sums, categorical breakdowns, empty dataset handling.
- **Policy RAG / CRAG (5)**: High-value review thresholds, international rules, failure procedures, human approval requirements.
- **Deterministic Risk (4)**: High-value domestic/international transfers, multi-signal scoring, completed low-risk activity.
- **Unsupported Inquiries (3)**: Out-of-domain queries (crypto, loyalty points) and non-existent database records.
- **Action & Approval Safety (3)**: Pending approval rejection, exact argument verification, single-use replay prevention.

### Core Scoring Principles
1. **Deterministic Properties Use Deterministic Scorers**: Numbers and flags are scored via exact programmatic matching (`exact_match`, `numeric_match`) — never by asking an LLM.
2. **Safety Invariants as Hard Gates**: A single approval bypass or unauthorized mutation is treated as a failed safety gate rather than an acceptable percentage point loss.
3. **Layered Evaluation**: Component evaluations run independently to isolate regressions before evaluating multi-agent workflows.

---

## 🚀 Production Backend Architecture

The FastAPI application follows a clean layered structure:

```
HTTP Request
    ↓
FastAPI Router  (src/app/api/routes/)
    ↓
Service Layer   (src/app/services/)
    ↓
LangGraph / Domain Capability
    ↓
Response Schema (src/app/api/schemas/)
```

Every HTTP request receives a unique `X-Request-ID` header via `RequestIDMiddleware`. Internal exceptions are never exposed to API consumers — they are mapped to structured error responses with the request ID.

---

## 📁 Project Structure

```
├── pyproject.toml              # Build config, ruff settings, pytest markers
├── Dockerfile                  # Production container (non-root user)
├── docker-compose.yml          # PostgreSQL 16 + Qdrant + Redis services
├── .dockerignore               # Excludes .env, .venv, __pycache__, tests, etc.
├── Makefile                    # Developer shortcuts (lint, test, docker)
├── requirements.txt            # Pinned production dependencies
├── ARCHITECTURE.md             # Architecture rules and dependency direction
├── AGENTS.md                   # Agent engineering standards & safety directives
├── .github/
│   └── workflows/
│       ├── ci.yml              # Lint → Unit Tests → Docker Build on every push/PR
│       ├── deploy-render.yml   # Render.com production deployment (CI-gated)
│       ├── deploy-aws.yml      # AWS deployment template
│       └── deploy-oracle.yml   # Oracle Cloud deployment template
├── data/
│   └── policies/               # Official compliance & risk policy documents
│       ├── account_restrictions.md
│       ├── failed_transactions.md
│       └── transaction_monitoring.md
├── docs/                       # Architecture diagrams and developer docs
├── infra/                      # Deployment-specific configuration (Render, Docker)
├── scripts/
│   ├── bootstrap.py            # One-shot: tables + checkpoints + seed + policies
│   ├── create_tables.py        # Initialize PostgreSQL schema
│   ├── seed_database.py        # Generate synthetic financial data
│   ├── index_policies.py       # Chunk and embed policies into Qdrant
│   ├── setup_memory_store.py   # Initialize long-term memory Qdrant collection
│   ├── smoke_test.py           # Live smoke test against running API
│   └── compare_rag_crag.py     # RAG vs. CRAG evaluation script
├── src/
│   ├── kit/                    # Domain-Independent Agent Infrastructure
│   │   ├── agents/             # Loop-controlled ReAct agent builder & executor nodes
│   │   ├── config/             # Pydantic Settings & environment variables
│   │   ├── context/            # Context categories, token estimator, priority builder
│   │   ├── crag/               # Evaluator, query rewriter, models, and pipeline
│   │   ├── databases/          # SQL AST validator, session pools, engines
│   │   ├── embeddings/         # OpenAI embedding provider adapters
│   │   ├── graphs/             # LangGraph PostgreSQL checkpointing helpers
│   │   ├── llms/               # ChatOpenAI factory, usage extractor, tracker, pricing registry
│   │   ├── loops/              # LoopController, budgets, action signatures, stop reasons
│   │   ├── mcp/                # MCP server infrastructure (MCPServer v2)
│   │   ├── memory/             # Memory record models, service, and vector store
│   │   ├── rag/                # Document models, chunkers, retrieval contracts
│   │   ├── tools/              # Abstract tool classes, registry, ControlledToolExecutor, retry policy
│   │   └── vectorstores/       # Qdrant client connection and collection helpers
│   └── app/                    # Domain-Specific Financial Intelligence Platform
│       ├── actions/            # Controlled mutations (freeze_account with audit)
│       ├── agents/             # Planner, SQL Analyst, Data Analyst, Policy, Risk, Report
│       ├── analytics/          # Deterministic computations (aggregations, sums, variance)
│       ├── api/
│       │   ├── routes/         # FastAPI routers: health, investigations, approvals, actions, memory
│       │   ├── schemas/        # Request/response schemas per route domain
│       │   ├── dependencies.py # Shared FastAPI dependency injection
│       │   ├── errors.py       # Error registry and HTTP status mapping
│       │   ├── middleware.py   # RequestIDMiddleware
│       │   └── router.py       # Root APIRouter aggregating all sub-routers
│       ├── core/               # ApplicationError, ResourceNotFoundError, ActionNotAllowedError
│       ├── db/                 # SQLAlchemy models & repositories (approvals, audit, accounts)
│       ├── graphs/             # LangGraph state graph, nodes, routers, dependencies
│       ├── mcp/                # MCP server adapter exposing platform capabilities
│       ├── prompts/            # Financial specialist system prompts
│       ├── rag/                # Policy document ingestion and retrieval
│       ├── risk/               # Deterministic risk scoring engine and signal models
│       ├── schemas/            # Shared Pydantic schemas (InvestigationPlan, Report, Actions)
│       ├── services/           # Investigation, approval, evidence, memory, SQL context services
│       ├── tools/              # SafeSQLTool, SchemaInspectorTool, DataAnalysisTool,
│       │                       # PolicyRetrievalTool, CorrectivePolicyRetrievalTool
│       └── main.py             # FastAPI app factory with lifespan, middleware, error handlers
└── tests/
    ├── conftest.py             # Deterministic fixtures & mock environment
    ├── integration/            # Real database and tool boundary tests
    │   ├── api/                # HTTP endpoint integration tests
    │   ├── app/
    │   │   ├── actions/        # Freeze account, single-use, rollback, denied-audit tests
    │   │   └── mcp/            # MCP server integration tests
    │   ├── database/           # Schema and repository tests
    │   └── kit/                # Kit infrastructure integration tests
    └── unit/                   # 152 unit tests covering all agents, nodes, tools, kit
        ├── app/
        │   ├── agents/         # Data analyst, policy agent, SQL loop, risk agent
        │   ├── api/            # Memory API endpoint tests
        │   ├── graphs/         # Graph build, routing, nodes, short-term memory
        │   ├── risk/           # Deterministic risk engine scoring
        │   ├── services/       # Evidence bundle, conversation context, memory, SQL context
        │   └── tools/          # Policy retrieval, CRAG, schema inspector, analytics
        └── kit/                # ReAct runtime, loop controller, context builder, pricing, tools
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.12+**
- **Docker & Docker Compose** (for PostgreSQL, Qdrant, and Redis)
- **OpenAI API Key**

### 1. Clone & Install

```bash
git clone https://github.com/zainexperience2005/financial-intelligence-risk-platform.git
cd financial-intelligence-risk-platform

# Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Install all dependencies (including dev)
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your OpenAI API key and database credentials
```

Key variables:

```env
ENVIRONMENT=development
DEBUG=false

LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_TEMPERATURE=0.0
OPENAI_API_KEY=your-openai-api-key-here

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=financial_policies

DATABASE_URL=postgresql+psycopg://financial_user:financial_password@localhost:5432/financial_platform
READ_ONLY_DATABASE_URL=postgresql+psycopg://financial_reader:financial_reader_password@localhost:5432/financial_platform
CHECKPOINT_DATABASE_URL=postgresql://financial_user:financial_password@localhost:5432/financial_platform
```

### 3. Start Infrastructure

```bash
docker compose up -d
```

Services:
- **PostgreSQL 16**: `localhost:5432`
- **Qdrant HTTP & Dashboard**: `http://localhost:6333/dashboard`
- **Redis**: `localhost:6379`

### 4. Bootstrap the Platform (One Command)

```bash
# Initializes tables, checkpoints, seeds data, and indexes policies
python scripts/bootstrap.py
```

Or step by step:

```bash
python scripts/create_tables.py       # PostgreSQL schema
python scripts/seed_database.py       # Synthetic financial data
python scripts/index_policies.py      # Compliance policy documents → Qdrant
python scripts/setup_memory_store.py  # Long-term memory Qdrant collection
```

### 5. Start the API Server

```bash
uvicorn app.main:app --reload --app-dir src --host 0.0.0.0 --port 8000
```

Interactive OpenAPI docs: `http://localhost:8000/docs`

---

## ⚡ API Reference

All endpoints are versioned under `/api/v1`.

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health/live` | Liveness probe |
| `GET` | `/api/v1/health/ready` | Readiness probe (checks DB) |

### Investigations

```bash
# POST /api/v1/investigations
curl -X POST http://localhost:8000/api/v1/investigations \
  -H "Content-Type: application/json" \
  -d '{"question": "Investigate transaction TX-1006.", "thread_id": "demo-001"}'

# Multi-turn follow-up (same thread_id)
curl -X POST http://localhost:8000/api/v1/investigations \
  -H "Content-Type: application/json" \
  -d '{"question": "Why was it considered high risk?", "thread_id": "demo-001"}'
```

Returns a structured `InvestigationReport` with executive summary, findings, policy citations, risk signals (`score`, `level`, `signals`), and `evidence_sufficient` / `policy_grounded` quality flags.

### Approvals

```bash
# Propose a protected action
curl -X POST http://localhost:8000/api/v1/actions/propose \
  -H "Content-Type: application/json" \
  -d '{"action": "freeze_account", "account_id": "ACC-1001", "reason": "High-risk international transfer."}'

# Inspect approval
curl http://localhost:8000/api/v1/approvals/{approval_id}

# Human review — approve
curl -X POST http://localhost:8000/api/v1/approvals/{approval_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"actor": "compliance_officer@example.com", "reason": "Verified alert."}'

# Human review — reject
curl -X POST http://localhost:8000/api/v1/approvals/{approval_id}/reject \
  -H "Content-Type: application/json" \
  -d '{"actor": "compliance_officer@example.com", "reason": "False positive."}'
```

### Actions

```bash
# Execute approved action (atomic: freeze + mark executed + audit)
curl -X POST http://localhost:8000/api/v1/actions/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "freeze_account", "account_id": "ACC-1001", "approval_id": "<id>", "executed_by": "analyst@example.com"}'
```

### Long-Term Memory

```bash
# Remember a finding (30-day retention)
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{"content": "TX-1006 was a high-risk international transfer.", "retention_days": 30}'

# Recall relevant historical findings
curl -X POST http://localhost:8000/api/v1/memory/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "international transfer risk", "k": 5}'

# Delete a memory record
curl -X DELETE http://localhost:8000/api/v1/memory/{memory_id}
```

---

## 🐳 Docker Deployment

Build and run the production container:

```bash
# Build
docker build -t firp:latest .

# Run with environment file
docker run -p 8000:8000 --env-file .env firp:latest
```

The container runs as a **non-root user** (`appuser`). Secrets are injected via environment variables — never baked into the image (enforced by `.dockerignore`).

---

## 🔄 CI/CD

Every push and pull request to `main`/`develop` runs the full CI pipeline:

```
Push / PR
    ↓
Ruff Lint Check
    ↓
115 Unit Tests (no infrastructure required)
    ↓
Docker Build Verification
    ↓
✅ Required to pass before merge
```

Production deployment to **Render** is a separate gated workflow triggered manually after CI passes — never automatic on PR.

---

## 🧪 Testing & Verification

```bash
# Run all 152 unit tests (offline, fast — no DB or LLM required)
pytest tests/unit

# Run with verbose output
pytest tests/unit -v

# Lint check
ruff check .

# Format check
ruff format --check .

# Run freeze_account integration tests (requires running PostgreSQL)
pytest tests/integration/app/actions/ -m postgres -v

# Smoke test against live API (requires running server)
python scripts/smoke_test.py
```

### Test Coverage Areas (161 Unit Tests)

| Area | Tests | Notes |
|---|---|---|
| **Risk Engine** | 3 | Deterministic score calculations |
| **Risk Agent** | 4 | `evidence_sufficient` semantics, `policy_grounded` separation |
| **Graph Nodes** | 11 | All nodes including multi-transaction risk guard |
| **Graph Routing** | 14 | All route combinations |
| **SQL Analyst Loop** | 4 | Loop state tracking |
| **Policy Agent** | 3 | CRAG evaluation, budget exhaustion |
| **Data Analyst** | 2 | Direct summary and tool execution |
| **Evidence Bundle** | 2 | Partial and complete bundles |
| **Memory Service** | 3 | Remember, recall, forget |
| **Conversation Context** | 3 | Bounded context window |
| **CRAG Pipeline** | 3 | Relevant/irrelevant/unanswerable paths |
| **SQL Validator** | 6 | SELECT-only, AST rejection, limit injection |
| **Tool Registry & Adapters** | 4 | Register, duplicate rejection, unknown tool, LangChain adapter |
| **Controlled Tool Executor** | 7 | Transient retry, permanent error, exception masking, normalization |
| **Loop Controller** | 11 | Iterations, tool calls, repeated actions, failures, token/cost budgets, fail-closed |
| **ReAct Agent Runtime** | 10 | Scenarios A/B/C/D, repeated actions, tool failure, token/cost/context budgets |
| **LLM Usage & Pricing** | 5 | Token extraction, cached cost, pricing registry, unknown cost |
| **Context Builder** | 4 | Priority selection, token estimation, overflow guard, headroom reserve |
| **SQL Model Context Service** | 2 | Row slicing and truncation metadata |
| **Golden Evaluation & Scorers** | 9 | Dataset schema, 24-case coverage, unique IDs, exact/numeric/source/grounding scorers |
| **Kit LLMs** | 4 | Config defaults, provider mapping |
| **Kit RAG** | 10 | Chunking, metadata, retrieval |
| **Data Analysis Tools** | 16 | Analytics schema, aggregation, group sum, counts |
| **Schema Inspector** | 3 | Table listing, column inspection, unknown table |
| **Policy Retrieval Tools** | 4 | Direct and corrective policy retrieval tools |
| **Memory API Endpoints** | 3 | FastAPI memory routes |
| **Financial Graph** | 2 | End-to-end multi-agent investigation graph |
| **Short-Term Memory** | 1 | Turn-scoped state isolation |
| **Dependencies & Setup** | 3 | Graph dependencies and memory app service |
| **Total** | **161** | **100% offline, deterministic, zero external API dependencies** |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.