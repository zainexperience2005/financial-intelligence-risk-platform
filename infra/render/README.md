# Render Deployment Infrastructure

This directory contains Render-specific configuration and deployment manifests.

## Target Architecture

- **Web Service**: FastAPI application container deployed from the repository root `Dockerfile`.
- **Managed PostgreSQL**: Persistent database instance for financial ledger, approvals, and LangGraph checkpoints.
- **Managed/Docker Qdrant**: Vector database service for policy document retrieval and memory storage.
- **Managed Redis**: Caching and background coordination.

## Configuration & Environment

Render services consume twelve-factor environment variables matching `.env.example`:
- `DATABASE_URL`
- `READONLY_DATABASE_URL`
- `CHECKPOINT_DATABASE_URL`
- `QDRANT_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`

Secrets must be supplied through the Render dashboard or API, never committed into version control.
