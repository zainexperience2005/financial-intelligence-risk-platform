# Financial Intelligence & Risk Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-dc2626.svg)](https://qdrant.tech/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)](https://github.com/astral-sh/ruff)

An enterprise-grade, production-oriented **Agentic AI platform for financial intelligence, fraud detection, and risk operations**.

The platform combines **LangGraph**, **PostgreSQL**, **Qdrant**, and a multi-agent topology to orchestrate structured investigation plans, secure read-only SQL retrieval, deterministic statistical data analysis, and **Corrective RAG (CRAG)** policy retrieval.

---

## 🏛️ Architectural Overview

The repository enforces a strict, clean architecture separating domain-independent agentic infrastructure from domain-specific financial intelligence:

```
src/
├── kit/       # Reusable Agentic AI Infrastructure (Domain-Independent)
└── app/       # Financial Intelligence & Risk Platform (Domain-Specific)
```

### Dependency Rules & Design Principles
- **Unidirectional Dependency Direction**: `app` depends on `kit`. `kit` **never** imports or depends on `app`.
- **Infrastructure Reusability**: All LLM provider adapters, database validation engines, vector store clients, RAG/CRAG pipelines, generic tool registries, and loop controls live in `kit`.
- **Domain Confinement**: Domain-specific prompts, database models (accounts, transactions, alerts), financial policies, and business workflows live strictly in `app`.
- **Deterministic Routing**: Decisions are routed using structured state variables and deterministic Python routers rather than redundant model calls.
- **Authoritative Data & Safety**: Model-generated queries never hit the database directly. All queries pass through an AST-based SQL validator and execute via a dedicated read-only role with single-statement constraints and strict execution budgets.
- **Deterministic Math**: Calculations are executed with Python and Pandas rather than probabilistic LLM arithmetic.
- **Corrective Policy Retrieval (CRAG)**: Retrieved policy evidence is actively graded for relevance. If evidence is weak or irrelevant, the query is rewritten and re-retrieved; if evidence is absent, the system explicitly marks the query as unanswerable rather than hallucinating policy rules.

---

## 🔄 Multi-Agent Investigation Workflow

The platform orchestrates financial investigations using a compiled **LangGraph** state graph:

```mermaid
flowchart TD
    START([START]) --> Planner[Planner Agent<br/>plan_investigation]
    
    Planner -->|requires_sql = true| SQL[SQL Analyst Agent<br/>analyze_sql]
    Planner -->|requires_sql = false| Analyze[Financial Analyst Agent<br/>analyze_question]
    
    SQL -->|requires_analytics = true| DataAnalyst[Data Analyst Agent<br/>analyze_data]
    SQL -->|requires_analytics = false & requires_policy = true| PolicyAgent[Policy Agent<br/>CRAG / analyze_policy]
    SQL -->|no analytics or policy| Analyze
    
    DataAnalyst -->|requires_policy = true| PolicyAgent
    DataAnalyst -->|requires_policy = false| Analyze
    
    PolicyAgent --> Analyze
    
    Analyze -->|requires_data = true| DataReq[Handle Data Requirement<br/>handle_data_requirement]
    Analyze -->|requires_data = false| END_NODE([END])
    
    DataReq --> END_NODE
```

### Agents & Specialist Roles

| Agent / Node | Primary Responsibility | Guardrails & Safety Controls |
|---|---|---|
| **Planner** | Evaluates user inquiry and produces a structured `InvestigationPlan` (determining whether SQL retrieval, data analytics, or policy grounding is required). | Outputs typed Pydantic plan; does not execute database queries or mutations directly. |
| **SQL Analyst** | Retrieves authoritative financial records from PostgreSQL. | Read-only SELECT enforcement, AST single-statement validation, repeated query detection, iteration and attempt limits. |
| **Data Analyst** | Runs deterministic computations (aggregations, sums, variances) over retrieved rows. | Uses explicit Python/Pandas operations rather than LLM calculation; bounded to tool-call budget. |
| **Policy Agent** | Grounds findings in official financial risk policies using **Corrective RAG (CRAG)**. | Treats retrieved documents as untrusted evidence; grades relevance; bounded query rewriting; cites verified chunk IDs. |
| **Financial Analyst** | Synthesizes retrieved records, calculated figures, and policy evidence into a comprehensive assessment. | Constrained to authoritative tool evidence; explicitly highlights missing records. |
| **Data Required** | Gracefully handles scenarios where necessary records are missing or ambiguous. | Returns actionable next steps without guessing or hallucinating financial facts. |

---

## 📚 Corrective RAG (CRAG) Architecture

In standard RAG, vector retrieval may technically return chunks, but they may be irrelevant or insufficient to answer the query. CRAG sits on top of baseline RAG as an active control layer:

```text
                    User Query
                        │
                        ▼
                 Vector Retrieval (Qdrant)
                        │
                        ▼
               Retrieval Evaluator (LLM Grader)
                        │
             ┌──────────┴──────────┐
             │                     │
          relevant            weak/irrelevant
             │                     │
             │                     ▼
             │                Query Rewriter
             │                     │
             │                     ▼
             │               Vector Retrieval (Retry)
             │                     │
             │                     ▼
             │               Re-evaluation
             │                     │
             │             ┌───────┴────────┐
             │             │                │
             │          usable       insufficient
             │             │                │
             └──────┬──────┘                │
                    ▼                       ▼
              Policy Evidence          Refuse to infer
```

- **Candidate Generation**: Qdrant vector search retrieves top-$k$ policy chunks.
- **Evidence Evaluation**: Evaluates whether retrieved evidence actually answers the specific query (`relevant`, `partial`, `irrelevant`).
- **Bounded Correction**: If evidence is weak, rewrites the retrieval query to better capture search intent and retries retrieval once (bounded to 1 attempt).
- **Answerability Check**: Evaluates whether final evidence is sufficient (`CRAGResult.answerable`). If insufficient, the Policy Agent explicitly refuses to guess, preventing policy hallucination.
- **Preserved Baseline**: The standard `PolicyRetrievalTool` remains intact to enable empirical quality comparisons against `CorrectivePolicyRetrievalTool`.

---

## 🔒 Security & Safety Guarantees

1. **AST-Based SQL Validation**: Queries are parsed with `sqlglot` to enforce single-statement `SELECT` operations only. Prohibits any `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, or administrative commands.
2. **Dedicated Read-Only Database Role**: Database connections execute with a dedicated `financial_reader` user with SELECT-only database permissions.
3. **Execution Budgets & Loop Controls**: Hard query timeouts, row count caps, maximum tool-call budgets, and repeated-query detection protect against denial of service and runaway loops.
4. **Deterministic Calculation Engine**: Arithmetic calculations are executed with typed analytics operations, preventing model hallucinations in financial risk scoring.

---

## 📁 Project Structure

```
├── pyproject.toml              # Build configuration and test dependencies
├── docker-compose.yml          # PostgreSQL 16 & Qdrant vector database services
├── ARCHITECTURE.md             # High-level architecture and dependency rules
├── AGENTS.md                   # Agent engineering standards and development guidelines
├── data/
│   └── policies/               # Approved financial policies (markdown)
│       ├── account_restrictions.md
│       ├── failed_transactions.md
│       └── transaction_monitoring.md
├── scripts/
│   ├── compare_rag_crag.py     # Compares baseline RAG with Corrective RAG
│   ├── create_tables.py        # PostgreSQL schema initialization
│   ├── index_policies.py       # Ingests & indexes policy markdown into Qdrant
│   ├── seed_database.py        # Generates synthetic accounts and transactions
│   ├── test_policy_agent.py    # Verification script for Policy Agent with CRAG
│   └── test_sql_analyst.py     # Verification script for SQL Analyst agent
├── src/
│   ├── kit/                    # Reusable Agentic AI Infrastructure (Domain-Independent)
│   │   ├── config/             # Pydantic Settings & environment loaders
│   │   ├── crag/               # Evaluator, query rewriter, models, and pipeline
│   │   ├── databases/sql/      # AST validator, connection managers, execution engine
│   │   ├── embeddings/         # OpenAI embeddings factory
│   │   ├── llms/               # ChatOpenAI provider factories and configuration
│   │   ├── rag/                # Document chunking, metadata models, and retrieval
│   │   ├── tools/              # Generic tool base classes, registry, LangChain adapters
│   │   └── vectorstores/       # Qdrant client connection and collection factories
│   └── app/                    # Financial Intelligence Platform (Domain-Specific)
│       ├── agents/             # Planner, SQL Analyst, Data Analyst, Policy Agent
│       ├── analytics/          # Deterministic analysis operations (sum, mean, etc.)
│       ├── api/                # FastAPI application, routes, and request models
│       ├── db/                 # Financial models (Accounts, Transactions, Alerts)
│       ├── graphs/             # LangGraph state graph, nodes, and deterministic routers
│       ├── prompts/            # Domain-specific agent system prompts
│       ├── schemas/            # Pydantic structured output models
│       └── tools/              # SafeSQLTool, SchemaInspectorTool, DataAnalysisTool,
│                               # PolicyRetrievalTool, CorrectivePolicyRetrievalTool
└── tests/
    ├── conftest.py             # Shared pytest fixtures
    ├── integration/            # Integration tests with database and tool boundary
    └── unit/                   # Comprehensive unit tests (80+ tests)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.12+**
- **Docker & Docker Compose** (for PostgreSQL and Qdrant)
- **OpenAI API Key**

### 2. Environment Setup

```bash
# Clone repository
git clone https://github.com/zainexperience2005/financial-intelligence-risk-platform.git
cd financial-intelligence-risk-platform

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install platform in editable mode
pip install -e .
```

### 3. Environment Configuration

Copy the example environment configuration:

```bash
cp .env.example .env
```

Set your credentials in `.env`:

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
```

### 4. Start Infrastructure with Docker Compose

Start PostgreSQL and Qdrant:

```bash
docker compose up -d
```

Services exposed:
- **PostgreSQL**: `localhost:5432`
- **Qdrant HTTP & Dashboard**: `http://localhost:6333/dashboard`
- **Qdrant gRPC**: `localhost:6334`

### 5. Initialize & Seed Database and Vector Knowledge Base

```bash
# Initialize PostgreSQL schema (Accounts, Transactions, Alerts)
python scripts/create_tables.py

# Seed database with sample financial records
python scripts/seed_database.py

# Index policy documents into Qdrant collection
python scripts/index_policies.py
```

---

## ⚡ Running the API & Verification Scripts

### Start the API Server

```bash
uvicorn app.main:app --reload --app-dir src --host 0.0.0.0 --port 8000
```

Access:
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`
- **Health Check**: `GET http://localhost:8000/health`
- **Chat Investigation Endpoint**: `POST http://localhost:8000/chat`

### Run Verification Scripts

```bash
# Verify Policy Agent with CRAG grounded retrieval
python scripts/test_policy_agent.py

# Compare baseline RAG with Corrective RAG on off-topic questions
python scripts/compare_rag_crag.py

# Verify SQL Analyst with SafeSQL
python scripts/test_sql_analyst.py
```

---

## 🧪 Testing & Quality Assurance

Run the comprehensive unit and integration test suite:

```bash
# Run all unit tests (fast, offline with mocked dependencies)
pytest

# Run tests with verbose output
pytest -v

# Run linting and code style checks
ruff check .
ruff format --check .
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.