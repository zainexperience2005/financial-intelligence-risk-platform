# Architecture

## Core Principle

This repository contains two major Python packages:

### `src/kit`

Reusable, domain-independent Agentic AI infrastructure.

Examples:

- LLM providers
- embeddings
- vector stores
- tools
- RAG
- CRAG
- memory
- LangGraph utilities
- MCP
- loop engineering
- evaluation
- observability
- security
- approval workflows

### `src/app`

Financial Intelligence & Risk Platform business logic.

Examples:

- financial agents
- transaction analysis
- risk rules
- financial database models
- finance-specific prompts
- financial workflows

## Dependency Rule

Allowed:

app -> kit

Forbidden:

kit -> app

The kit must never depend on Financial Intelligence
application code.

## Reusability Rule

Before adding code to kit, ask:

"Could another unrelated Agentic AI application use this?"

If yes, it may belong in kit.

If no, it belongs in app.