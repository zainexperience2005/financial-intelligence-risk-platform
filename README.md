# Financial Intelligence & Risk Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-dc2626.svg)](https://qdrant.tech/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)](https://github.com/astral-sh/ruff)

An enterprise-grade, production-oriented **Agentic AI platform for financial intelligence, fraud investigation, and controlled risk mitigation**.

The platform integrates **LangGraph multi-agent orchestration**, **PostgreSQL**, **Qdrant**, **AST-validated SafeSQL**, **Corrective RAG (CRAG)**, a **deterministic risk engine**, and a **tamper-evident human-in-the-loop approval & audit workflow** with real, controlled database mutations.

---

## 🏛️ Architectural Overview

The repository strictly enforces a clean architectural separation between domain-independent agentic infrastructure and domain-specific financial intelligence:

```
src/
├── kit/       # Reusable Agentic AI Infrastructure (Domain-Independent)
└── app/       # Financial Intelligence & Risk Platform (Domain-Specific)
```

### Dependency Rules & Design Principles
- **Unidirectional Dependency Direction**: `app` depends on `kit`. `kit` **never** imports or depends on `app`.
- **Infrastructure Reusability**: LLM provider factories, SQL AST validation engines, vector store clients, RAG/CRAG pipelines, generic tool registries, and loop controls live in `kit`.
- **Domain Confinement**: Domain-specific prompts, database models (accounts, transactions, approval records, audit events), financial policy ingestion, risk rule evaluation, and business workflows live strictly in `app`.
- **Deterministic Routing**: Workflow routing is driven by structured state variables and deterministic Python conditions rather than redundant LLM router calls.
- **Authoritative Evidence Separation**: Specialist agents retrieve and compute authoritative facts. The report synthesis agent explains and contextualizes verified evidence without recalculating or inventing numbers.
- **Strict Trust Boundary**: Models may recommend actions, but they **never** hold direct database write access or bypass human review.

---

## 🔄 Multi-Agent Investigation Topology

The platform coordinates specialized autonomous agents in a compiled **LangGraph** state graph:

```mermaid
flowchart TD
    START([START]) --> PrepareTurn[Prepare Turn<br/>prepare_turn<br/>Resets Turn-Scoped Evidence]
    PrepareTurn --> Planner[Planner Agent<br/>plan_investigation<br/>+ Bounded Conversation Context]
    
    Planner -->|requires_sql = true| SQL[SQL Analyst Agent<br/>analyze_sql]
    Planner -->|requires_sql = false| AnalyzePolicy{requires_policy?}
    
    SQL -->|requires_analytics = true| DataAnalyst[Data Analyst Agent<br/>analyze_data]
    SQL -->|requires_analytics = false & requires_policy = true| PolicyAgent[Policy Agent<br/>CRAG / analyze_policy]
    SQL -->|no analytics or policy| RiskCheck{requires_risk?}
    
    DataAnalyst -->|requires_policy = true| PolicyAgent
    DataAnalyst -->|requires_policy = false| RiskCheck
    
    PolicyAgent --> RiskCheck
    
    RiskCheck -->|requires_risk = true| RiskAgent[Deterministic Risk Engine<br/>& Risk Agent]
    RiskCheck -->|requires_risk = false| ReportAgent[Report Synthesis Agent<br/>Investigation Report]
    
    RiskAgent --> ReportAgent
    
    ReportAgent --> END_NODE([END])
```

### Agents & Specialist Roles

| Agent / Node | Primary Responsibility | Guardrails & Safety Controls |
|---|---|---|
| **Planner Agent** | Analyzes inquiries and generates a typed `InvestigationPlan` establishing whether SQL retrieval, data analytics, policy grounding, or risk evaluation are needed. | Outputs structured Pydantic plan; performs no database access or analytical computation directly. |
| **SQL Analyst Agent** | Retrieves authoritative financial records (accounts, transactions, customers). | AST single-statement validation (`sqlglot`), read-only SELECT enforcement, iteration budgets, and repeated-action detection. |
| **Data Analyst Agent** | Computes statistical aggregations, sums, counts, and variance over retrieved rows. | Executes purely deterministic Python/Pandas operations; bounded by strict tool-call limits. |
| **Policy Agent** | Grounds findings in official financial risk policies using **Corrective RAG (CRAG)**. | Evaluates candidate relevance; triggers bounded query rewriting if weak; refuses to guess if unanswerable. |
| **Risk Agent** | Evaluates rule-based signals and risk thresholds against retrieved evidence. | Scores and flags are computed strictly by deterministic application code, never fabricated by the LLM. |
| **Report Agent** | Synthesizes specialist findings into an analyst-ready `InvestigationReport`. | Derives citations and findings solely from authoritative evidence; cannot execute operational mutations. |

---

## 🛡️ Controlled Actions, Human Approvals & Persistent Audit Trail

One of the platform's core architectural achievements is crossing the boundary from passive investigation into **real, controlled customer-impacting database mutations** while preserving an absolute trust boundary:

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
   - `financial_reader`: Dedicated SELECT-only PostgreSQL user used by `SafeSQLTool`. Can read business tables (`customers`, `accounts`, `transactions`) but is **strictly denied** `SELECT` access on `approval_requests` and `audit_events`.
   - `financial_user`: Read/write application credentials used exclusively by deterministic application repositories. Never exposed to models.
2. **Deterministic Pre-Execution Verification**:
   Before executing an action, the application enforces:
   - Approval exists and has `status == "approved"`.
   - Action name matches exactly (e.g., `freeze_account`).
   - Action arguments match exactly (e.g., `account_id` target).
   - Single-use consumption (replays or previously executed approvals are rejected).
3. **Atomic Single-Transaction Execution**:
   The account mutation, approval execution mark, and audit event creation are executed inside a **single database transaction** with explicit rollback on error, preventing partial or orphaned state changes:
   ```python
   try:
       freeze_account_record(account)
       mark_approval_executed(approval)
       record_audit_event(session, ...)
       session.commit()
   except Exception:
       session.rollback()
       raise
   ```
4. **Tamper-Evident Audit Trail**:
   Every state change (`approval_requested`, `approval_approved`, `approval_rejected`, `action_executed`, `action_failed`) is permanently recorded in PostgreSQL with timestamp, actor, entity ID, and context metadata.

---

## 🧠 Persistent Short-Term Memory with LangGraph Checkpointing

The platform persists conversation context across turns using **PostgreSQL checkpointing (`PostgresSaver`)**, allowing analysts to ask follow-up questions (e.g. resolving pronouns like *"Why was it high risk?"*) while enforcing strict context boundaries:

```text
Turn 1: "Investigate TX-1006."
  └─► Planner retrieves TX-1006 records, evaluates risk, synthesizes report
  └─► Executive summary saved to conversation thread (AIMessage)

Turn 2: "Why was it considered high risk?" (same thread_id)
  └─► prepare_turn resets previous specialist evidence (SQL, analytics, policies, report)
  └─► Planner receives bounded recent conversation window (last 6 messages)
  └─► Planner resolves "it" -> "TX-1006" and orchestrates targeted verification
```

### Memory Engineering Rules
1. **Thread Identity != User Identity**: A `thread_id` identifies a specific investigation thread. Different `thread_id` values remain strictly isolated.
2. **Turn-Scoped Specialist State vs. Persistent Context**:
   - `messages`: Accumulated across turns via the `add_messages` reducer.
   - Specialist evidence (`plan`, `sql_analysis`, `data_analysis`, `policy_analysis`, `risk_analysis`, `report`): Cleaned by `prepare_turn` at the start of each turn so stale findings are never mistaken for fresh evidence.
3. **Memory is Context, Not Authoritative Authority**: Previous assistant statements provide semantic reference for coreference resolution, but live transactions and policy citations must always be verified afresh through controlled tools.
4. **Bounded Context Windows**: `format_recent_context()` bounds recent context to the last 6 messages, preventing context window bloat and runaway token costs.

---

## 💾 Durable Long-Term Memory with Qdrant

While short-term memory tracks conversation context within a single investigation thread, **long-term memory selectively persists durable findings and context across investigations** in a dedicated Qdrant collection (`financial_memory`):

| Capability | Storage System | Semantics & Purpose | Lifecycle |
|---|---|---|---|
| **Short-Term Memory** | PostgreSQL Checkpointer | Turn-to-turn thread dialogue (`thread_id`) | Active investigation thread |
| **Long-Term Memory** | Qdrant (`financial_memory`) | Selective historical findings, summaries | Explicit retention (`retention_days`) & deletion |
| **Policy RAG / CRAG** | Qdrant (`financial_policies`) | Authoritative, approved compliance rules | Version-controlled, static documents |
| **Transactional Facts** | PostgreSQL (Relational) | Authoritative ground truth (accounts, balances) | Audited, ACID transactions |

### Long-Term Memory Principles
- **Selective Persistence**: We do not blindly dump entire conversations into vector storage. Only concise, attributable investigation summaries are stored.
- **Explicit Expiration**: Every memory record supports an optional `expires_at` timestamp. Queries automatically filter out expired records.
- **Auditable & Deletable**: Every record has a stable `memory_id` UUID, enabling immediate deletion (`DELETE /memory/{id}`).
- **Privacy & Security Boundaries**: Long-term memory never stores credentials, approval tokens, connection strings, or unnecessary PII.

---

## 📚 Corrective RAG (CRAG) Architecture

Standard vector retrieval can return chunks that match keywords but fail to answer the financial policy question. CRAG adds an evaluation and correction loop:

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
              │                             ▼
              │                      Vector Retrieval
              │                             │
              │                             ▼
              │                      Re-evaluation
              │                             │
              │                     ┌───────┴───────┐
              │                     │               │
              │                  Usable        Insufficient
              │                     │               │
              └──────────────┬──────┘               │
                             ▼                      ▼
                       Policy Evidence      Refuse to Hallucinate
```

- **Relevance Grading**: Chunks are scored as `relevant`, `partial`, or `irrelevant`.
- **Bounded Correction**: If initial chunks are weak, the query is rewritten and retrieval is re-executed once (bounded retry budget).
- **Answerability Guard**: If evidence remains insufficient, the agent outputs an explicit refusal rather than fabricating policy thresholds.

---

## 📁 Project Structure

```
├── pyproject.toml              # Build configuration, ruff settings, pytest markers
├── docker-compose.yml          # PostgreSQL 16 & Qdrant vector database services
├── ARCHITECTURE.md             # Clean architecture and dependency rules
├── AGENTS.md                   # Agent engineering standards & safety directives
├── data/
│   └── policies/               # Official compliance & risk policy documents
│       ├── account_restrictions.md
│       ├── failed_transactions.md
│       └── transaction_monitoring.md
├── scripts/
│   ├── compare_rag_crag.py     # Compares standard RAG vs. Corrective RAG
│   ├── create_tables.py        # Initializes PostgreSQL schema and tables
│   ├── index_policies.py       # Chunks and embeds policy documents into Qdrant
│   ├── seed_database.py        # Generates synthetic customers, accounts, and transactions
│   ├── test_policy_agent.py    # Standalone verification for Policy Agent with CRAG
│   └── test_sql_analyst.py     # Standalone verification for SQL Analyst Agent
├── src/
│   ├── kit/                    # Domain-Independent Agent Infrastructure
│   │   ├── approvals/          # Generic human approval data schemas
│   │   ├── config/             # Pydantic Settings & environment variables
│   │   ├── crag/               # Evaluator, query rewriter, models, and pipeline
│   │   ├── databases/          # SQL AST validator, connection pools, engines
│   │   ├── embeddings/         # OpenAI embedding provider adapters
│   │   ├── llms/               # ChatOpenAI factory and completion wrappers
│   │   ├── rag/                # Document models, chunkers, retrieval contracts
│   │   ├── tools/              # Abstract tool classes, registry, LangChain adapters
│   │   └── vectorstores/       # Qdrant client connection and collection helpers
│   └── app/                    # Domain-Specific Financial Intelligence Platform
│       ├── actions/            # Controlled mutations (freeze_account)
│       ├── agents/             # Planner, SQL Analyst, Data Analyst, Policy, Risk, Report
│       ├── analytics/          # Deterministic computations (aggregations, sums, variances)
│       ├── api/                # FastAPI routers: /chat, /actions, /approvals
│       ├── db/                 # Models & Repositories (approvals, audit, accounts)
│       ├── graphs/             # LangGraph state graph, nodes, and deterministic routers
│       ├── prompts/            # Financial specialist prompts & system instructions
│       ├── risk/               # Deterministic risk scoring engine
│       ├── schemas/            # Structured outputs (InvestigationPlan, Report, Actions)
│       ├── services/           # Evidence collection and persistent approval services
│       └── tools/              # SafeSQLTool, SchemaInspectorTool, DataAnalysisTool,
│                               # PolicyRetrievalTool, CorrectivePolicyRetrievalTool
└── tests/
    ├── conftest.py             # Deterministic test fixtures & mock environment
    ├── integration/            # Real database and tool boundary tests
    │   ├── actions/            # Freeze account, single-use, rollback, and audit tests
    │   └── tools/              # SafeSQL execution and permission tests
    └── unit/                   # 90+ comprehensive unit tests covering all agents and nodes
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.12+**
- **Docker & Docker Compose** (for PostgreSQL and Qdrant)
- **OpenAI API Key**

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/zainexperience2005/financial-intelligence-risk-platform.git
cd financial-intelligence-risk-platform

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e .
```

### 3. Environment Configuration

Create a `.env` file based on `.env.example`:

```env
ENVIRONMENT=development
DEBUG=false

# LLM & Embeddings Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_TEMPERATURE=0.0
OPENAI_API_KEY=your-openai-api-key-here

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

# Vector Database (Qdrant)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=financial_policies

# Relational Database (PostgreSQL)
DATABASE_URL=postgresql+psycopg://financial_user:financial_password@localhost:5432/financial_platform
READ_ONLY_DATABASE_URL=postgresql+psycopg://financial_reader:financial_reader_password@localhost:5432/financial_platform
CHECKPOINT_DATABASE_URL=postgresql://financial_user:financial_password@localhost:5432/financial_platform
```

### 4. Start Infrastructure with Docker Compose

```bash
docker compose up -d
```

Services exposed:
- **PostgreSQL 16**: `localhost:5432`
- **Qdrant HTTP & Dashboard**: `http://localhost:6333/dashboard`
- **Qdrant gRPC**: `localhost:6334`

### 5. Initialize & Seed Knowledge Bases

```bash
# 1. Initialize PostgreSQL tables (accounts, customers, transactions, approvals, audit)
python scripts/create_tables.py

# 2. Setup LangGraph persistent checkpointing tables
python scripts/setup_checkpoints.py

# 3. Seed synthetic financial data
python scripts/seed_database.py

# 4. Ingest and index compliance policies into Qdrant
python scripts/index_policies.py

# 5. Initialize dedicated Qdrant long-term memory collection
python scripts/setup_memory_store.py
```

---

## ⚡ API Endpoints & Usage

Start the development server:

```bash
uvicorn app.main:app --reload --app-dir src --host 0.0.0.0 --port 8000
```

Interactive OpenAPI docs: `http://localhost:8000/docs`

### 1. Multi-Turn Financial Investigation (`POST /investigate` or `POST /chat`)
Submits a query to the multi-agent investigation graph with conversation thread persistence:

```bash
# Turn 1: Initial inquiry on thread demo-001
curl -X POST http://localhost:8000/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Investigate transaction TX-1006.",
    "thread_id": "demo-001"
  }'

# Turn 2: Follow-up inquiry referencing previous context
curl -X POST http://localhost:8000/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why was it considered high risk?",
    "thread_id": "demo-001"
  }'
```

Returns a structured `InvestigationReport` with executive summary, authoritative findings, policy citations, calculated risk signals, and recommendations.

### 2. Propose an Action (`POST /actions/propose`)
Creates a pending approval request and writes an audit event:

```bash
curl -X POST http://localhost:8000/actions/propose \
  -H "Content-Type: application/json" \
  -d '{
    "action": "freeze_account",
    "account_id": "ACC-1001",
    "reason": "Suspicious transaction frequency exceeds risk threshold."
  }'
```

### 3. Human Approval Workflow
- **Inspect**: `GET /approvals/{approval_id}`
- **Approve**:
  ```bash
  curl -X POST http://localhost:8000/approvals/{approval_id}/approve \
    -H "Content-Type: application/json" \
    -d '{"decided_by": "compliance_officer@example.com", "reason": "Verified alert."}'
  ```
- **Reject**:
  ```bash
  curl -X POST http://localhost:8000/approvals/{approval_id}/reject \
    -H "Content-Type: application/json" \
    -d '{"decided_by": "compliance_officer@example.com", "reason": "False positive."}'
  ```

### 4. Execute Controlled Action (`POST /actions/execute`)
Executes the approved action within an atomic database transaction:

```bash
curl -X POST http://localhost:8000/actions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "freeze_account",
    "account_id": "ACC-1001",
    "approval_id": "<approval_id>",
    "executed_by": "analyst@example.com"
  }'
```

### 5. Durable Long-Term Memory (`/memory`)
Store, search, and delete selective investigation findings:

```bash
# Remember finding with 30-day retention
curl -X POST http://localhost:8000/memory \
  -H "Content-Type: application/json" \
  -d '{"content": "Investigation TX-1006 identified high risk international transfer.", "retention_days": 30}'

# Recall relevant historical findings
curl -X POST http://localhost:8000/memory/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "international transfer risk", "k": 5}'

# Delete memory by ID
curl -X DELETE http://localhost:8000/memory/{memory_id}
```

---

## 🧪 Testing & Verification

The platform maintains a comprehensive test suite across unit and integration levels:

```bash
# Run all unit tests (offline, fast)
pytest tests/unit

# Run action integration tests
pytest tests/integration/app/actions/test_freeze_account.py

# Run all tests
pytest tests/unit tests/integration/app/actions/test_freeze_account.py

# Verify code formatting and linting
ruff check .
ruff format --check .
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.