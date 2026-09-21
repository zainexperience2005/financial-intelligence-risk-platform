# ADR-001: Financial Investigation Agent Architecture

## Status

Accepted

## Context

The Financial Intelligence & Risk Platform requires
LLM reasoning, SQL analysis, policy retrieval, deterministic
risk scoring, reporting, approval-controlled actions, memory,
and MCP-based capabilities.

A fully autonomous ReAct agent would provide flexibility but
would place too much workflow sequencing under model control.

A fully deterministic workflow would provide control but
would reduce useful semantic reasoning and planning.

## Decision

Use a hybrid LangGraph architecture.

LLMs are responsible for semantic planning, SQL generation
within controlled boundaries, policy interpretation, and
evidence synthesis.

Deterministic application code is responsible for workflow
dependencies, routing constraints, SQL validation, risk
scoring, approval enforcement, mutations, and auditing.

Specialist agents receive only the capabilities required for
their responsibilities.

MCP may provide capabilities to specialists but does not
change workflow authorization or safety boundaries.

## Consequences

Benefits:

- explicit workflow
- easier testing
- auditable execution
- controlled tool access
- deterministic safety boundaries
- replaceable specialist implementations

Trade-offs:

- more orchestration code
- less agent autonomy
- workflow changes require graph changes
- more state contracts must be maintained
