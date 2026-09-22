# ADR-002: Evidence Authority

## Status

Accepted

## Context

Reports may receive current SQL rows, deterministic calculations, current policy retrieval, historical memory, and conversation context. Treating these sources as equally authoritative would permit stale memories, prior assistant claims, or outdated policy interpretations to override current evidence.

## Decision

Current verified SQL and deterministic computation take precedence over historical memory and conversation context. Policy claims require current policy retrieval and citation metadata. Specialist outputs remain turn-scoped; checkpointed conversation state does not make previous financial evidence current. Missing or contradictory evidence must be represented as a limitation.

## Alternatives Considered

- Treat every context item supplied to the LLM equally.
- Let the report model reconcile conflicting sources without explicit priority.
- Reuse checkpointed specialist evidence on later turns.

## Consequences

Reports remain traceable to authoritative sources and are less likely to repeat stale or hallucinated claims. The system must re-query current data when authority matters, explicitly budget evidence context, and maintain source metadata.
