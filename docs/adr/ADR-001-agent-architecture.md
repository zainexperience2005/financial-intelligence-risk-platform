# ADR-001: Financial Investigation Agent Architecture

## Status

Accepted

## Context

The platform needs semantic planning, controlled data access, policy retrieval, deterministic analytics and risk scoring, grounded reporting, memory, and approval-controlled operations. A single autonomous agent would place sequencing and too many capabilities under model control, while a completely deterministic pipeline would lose useful semantic interpretation.

## Decision

Use a hybrid Planner/Specialist LangGraph architecture. LLMs perform semantic planning, bounded SQL generation, policy interpretation, and evidence synthesis. Deterministic application code normalizes dependencies, routes the workflow, validates SQL, performs analytics and risk scoring, enforces resource limits and approvals, executes mutations, and records audits.

Specialists receive only the capabilities required for their responsibility. The report agent receives evidence but no operational tools. MCP can deliver capabilities without changing workflow authorization.

## Alternatives Considered

- One general-purpose ReAct agent with every tool.
- A completely deterministic pipeline with no semantic planner.
- Independent specialists coordinating without a controlling graph.

## Consequences

The workflow is explicit, testable, auditable, and preserves deterministic safety boundaries. Specialist implementations remain replaceable. The tradeoffs are more orchestration code, less unconstrained autonomy, explicit state contracts, and graph changes when workflow structure changes.
