# Observability Architecture

This document describes the observability, tracing, and evaluation architecture of the Financial Intelligence & Risk Platform.

The platform maintains a strict separation across three distinct observability tiers:

```text
┌─────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY TIERS                    │
├──────────────────────────────┬──────────────────────────────┤
│ 1. Application Logs          │ 2. LangSmith AI Tracing      │
│    - HTTP & service logs     │    - Multi-agent graph spans │
│    - Request correlation     │    - Tool calls & latency    │
│    - Errors & health checks  │    - Token & cost tracking   │
│    - Transport debugging     │    - Golden set experiments  │
├──────────────────────────────┴──────────────────────────────┤
│ 3. PostgreSQL Audit Log                                     │
│    - Authoritative, immutable operational record            │
│    - Single-use approval creation, review, and execution   │
│    - Exact action argument binding & forensic accountability│
└─────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> A LangSmith trace is an engineering inspection tool; it is **NOT** the authoritative record for regulatory actions. The PostgreSQL audit trail remains the sole authoritative record for customer-impacting mutations.

---

## 1. Trace Correlation Keys

To trace an inquiry from HTTP entry down to agent loops without leaking state across conversations:

| Key | Purpose | Scope | Example |
|---|---|---|---|
| `request_id` | Correlates HTTP requests, server logs, and AI spans | Single API request | `550e8400-e29b-41d4-a716-446655440000` |
| `thread_id` | Identifies multi-turn dialogue continuity in LangGraph | Multi-turn thread | `eval-TX-1006` or `session-77a` |
| `component` | Identifies the specialist agent or infrastructural module | Single execution node | `financial_planner`, `policy_agent` |

### Header Injection
The FastAPI `RequestIDMiddleware` checks incoming `X-Request-ID` headers or generates a UUIDv4. This ID is attached to `request.state.request_id`, returned on the HTTP response header, and passed to `InvestigationService` to configure LangGraph metadata:

```python
config = {
    "tags": ["financial", "planner", f"request:{request_id}"],
    "metadata": {"request_id": request_id, "thread_id": thread_id},
    "configurable": {"thread_id": thread_id},
}
```

---

## 2. Secrets and PII Sanitization

Trace metadata must **never** become an unconstrained data or credentials dump:
- **Redacted Keys**: Any metadata key matching `password`, `secret`, `api_key`, `token`, `database_url`, or `credentials` is automatically replaced with `[REDACTED]` via `sanitize_metadata`.
- **PII Minimization**: Never include customer names, account numbers, credit card details, or full SQL records in trace tags.
- **Tool Traces**: Record deterministic metadata (e.g. `row_count`, `latency`, `sanitized_error_code`) rather than dumping full multi-megabyte payloads.

---

## 3. LangSmith Experiments & Golden Datasets

Evaluation experiments are conducted against version-controlled datasets stored in the repository:

1. **Source of Truth**: `evals/datasets/financial_golden.json` is version-controlled in Git.
2. **Synchronization**: `python scripts/sync_langsmith_dataset.py` syncs the dataset to `financial-intelligence-golden-v1` in LangSmith.
3. **Experiment Execution**: `LangSmithExperimentRunner` runs test cases through the workflow, measuring:
   - Routing accuracy (`requires_sql`, `requires_policy`, `requires_risk`)
   - Deterministic risk engine scores and signal codes
   - Source recall for policy citations
   - `GroundingJudge` semantic evaluation (verifying high risk is not conflated with fraud, and recommendations are not claimed as executed)
   - Latency, input tokens, output tokens, and spend ceilings

---

## 4. Safety Gates vs. Quality Metrics

| Category | Type | Failure Behavior |
|---|---|---|
| **Quality Metrics** | Average / Percentile | Low score signals need for optimization (e.g. prompt tuning, retrieval adjustments) |
| **Safety Invariants** | Hard Gate (0 tolerance) | **1 failure terminates release** (e.g. approval bypass, write via read-only SQL, argument substitution) |
