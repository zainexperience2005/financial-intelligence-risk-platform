# Financial Intelligence & Risk Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)](https://github.com/astral-sh/ruff)

An enterprise-grade, production-oriented **Agentic AI platform for financial intelligence, fraud detection, and risk operations**. 

The platform leverages **LangGraph**, **Pydantic**, and a multi-agent topology to orchestrate structured investigation plans, secure read-only SQL retrieval, and deterministic statistical data analysis.

---

## 🏛️ Architectural Overview

The repository is built around a strict separation of concerns between domain-independent agentic infrastructure and domain-specific financial intelligence:

```
src/
├── kit/       # Reusable Agentic AI Infrastructure (Domain-Independent)
└── app/       # Financial Intelligence & Risk Platform (Domain-Specific)
```

### Dependency Rules & Design Principles
- **Unidirectional Flow**: `app` depends on `kit`. `kit` **never** imports or depends on `app`.
- **Infrastructure Reusability**: All LLM provider adapters, database validation engines, generic tool registries, and loop controls live in `kit`.
- **Domain Confinement**: Domain-specific prompts, database models (accounts, transactions, alerts), and financial business rules live strictly in `app`.
- **Deterministic Routing**: Decisions are routed using structured state variables and deterministic Python routers rather than redundant model calls.
- **Safety First**: Model-generated queries never hit the database directly. All queries pass through an AST-based SQL validator and execute via a dedicated read-only role with single-statement constraints and execution limits.

---

## 🔄 Investigation Workflow

The platform orchestrates multi-agent investigations using a compiled **LangGraph** state graph:

```mermaid
flowchart TD
    START([START]) --> Planner[Planner Agent<br/>plan_investigation]
    
    Planner -->|requires_sql = true| SQL[SQL Analyst Agent<br/>analyze_sql]
    Planner -->|requires_sql = false| Analyze[Financial Analyst Agent<br/>analyze_question]
    
    SQL -->|requires_analytics = true| DataAnalyst[Data Analyst Agent<br/>analyze_data]
    SQL -->|requires_analytics = false| Analyze
    
    DataAnalyst --> Analyze
    
    Analyze -->|requires_data = true| DataReq[Handle Data Requirement<br/>handle_data_requirement]
    Analyze -->|requires_data = false| END_NODE([END])
    
    DataReq --> END_NODE
```

### Agents & Roles

| Agent / Node | Primary Responsibility | Guardrails & Safety |
|---|---|---|
| **Planner** | Evaluates user inquiry and produces an `InvestigationPlan` (determining if SQL retrieval or data analytics is required). | Generates structured Pydantic plan; does not execute queries or mutations directly. |
| **SQL Analyst** | Retrieves authoritative financial data from the database. | Read-only enforcement, AST single-statement validation, repeated query detection, iteration and attempt limits. |
| **Data Analyst** | Runs deterministic computations (aggregations, sums, variances) over retrieved rows. | Uses explicit tool-based calculations (Pandas/Python) rather than probabilistic LLM math; bounds tool calls to budget. |
| **Financial Analyst** | Synthesizes retrieved evidence, findings, and calculations into a coherent risk assessment. | Constrained to authoritative tool evidence; flags missing data explicitly. |
| **Data Required** | Gracefully handles scenarios where necessary records are missing or ambiguous. | Returns actionable next steps without hallucinating financial facts. |

---

## 🔒 Security & Safe SQL Architecture

1. **AST-Based Query Validation**: Queries are parsed with `sqlglot` to verify that they are single-statement `SELECT` operations. Prohibits any `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, or administrative commands.
2. **Read-Only Database Credentials**: The database engine runs with a dedicated read-only user (`financial_reader`) with SELECT-only privileges.
3. **Execution Limits**: Hard query timeouts, row count limits, and agent iteration budgets protect against denial of service and runaway loops.
4. **Deterministic Calculation**: Numeric analyses are offloaded to isolated deterministic analytics tools, preventing model hallucinations in financial risk scoring.

---

## 📁 Project Structure

```
├── pyproject.toml              # Build, dependencies, and tooling configuration
├── ARCHITECTURE.md             # High-level architecture and dependency guidelines
├── AGENTS.md                   # Agent engineering standards and development rules
├── scripts/
│   ├── create_tables.py        # Database schema initialization
│   ├── seed_database.py        # Synthetic financial data generator
│   └── test_sql_analyst.py     # Verification script for SQL analyst agent
├── src/
│   ├── kit/                    # Reusable Agentic AI Infrastructure
│   │   ├── config/             # Pydantic Settings & environment loaders
│   │   ├── databases/sql/      # AST validator, connection managers, execution engine
│   │   ├── llms/               # Provider factories (OpenAI, ChatOpenAI)
│   │   └── tools/              # Generic tool base classes, registry, LangChain adapters
│   └── app/                    # Financial Risk Platform
│       ├── agents/             # Planner, SQL Analyst, Data Analyst agents & loop states
│       ├── analytics/          # Deterministic analysis engines
│       ├── api/                # FastAPI application, routes, and request models
│       ├── db/                 # Financial models (Accounts, Transactions, Alerts, Risk Profiles)
│       ├── graphs/             # LangGraph state graph, nodes, and deterministic routers
│       ├── prompts/            # Financial system prompts
│       ├── schemas/            # Pydantic response models (InvestigationPlan, SQLAnalysisResult, etc.)
│       └── tools/              # SafeSQLTool, SchemaInspectorTool, DataAnalysisTool
└── tests/
    ├── integration/            # Integration tests with database and tool boundary
    └── unit/                   # Unit test suite for agents, graphs, kit, and validators
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.12+**
- **PostgreSQL 15+** (or Docker for containerized PostgreSQL)

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
# Clone repository
git clone https://github.com/zainexperience2005/financial-intelligence-risk-platform.git
cd financial-intelligence-risk-platform

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### 3. Environment Configuration

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
ENVIRONMENT=development
DEBUG=false

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_TEMPERATURE=0.0
OPENAI_API_KEY=your-openai-api-key-here

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql+psycopg://financial_user:financial_password@localhost:5432/financial_platform
READ_ONLY_DATABASE_URL=postgresql+psycopg://financial_reader:financial_reader_password@localhost:5432/financial_platform
```

### 4. Database Setup & Seeding

Initialize the schema and seed synthetic data for testing:

```bash
# Create tables (Accounts, Transactions, Alerts, Risk Profiles)
python scripts/create_tables.py

# Seed database with sample transactions and entities
python scripts/seed_database.py
```

---

## ⚡ Running the Application

### Start the API Server

```bash
uvicorn app.main:app --reload --app-dir src --host 0.0.0.0 --port 8000
```

The service exposes:
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`
- **Health Check**: `GET http://localhost:8000/health`
- **Investigation Chat Endpoint**: `POST http://localhost:8000/chat`

### Example Investigation Request

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Identify all high-risk wire transactions over $100,000 in the past 30 days and analyze total volume by beneficiary country."}'
```

---

## 🧪 Testing & Quality Assurance

Run the comprehensive unit and integration test suite:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/app --cov=src/kit

# Run code style and linting checks
ruff check .
ruff format --check .
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.