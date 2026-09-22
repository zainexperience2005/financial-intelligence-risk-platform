# ADR-003: Memory Boundaries

## Status

Accepted

## Context

Conversation continuity, historical investigation context, current financial state, and policy knowledge have different authority, retention, deletion, and query requirements. A single vector store would blur those boundaries.

## Decision

Use separate stores and lifecycles:

- Short-term workflow state: LangGraph checkpoints in PostgreSQL.
- Long-term historical investigation context: a dedicated Qdrant memory collection.
- Current operational state: PostgreSQL business tables.
- Policy knowledge: a dedicated Qdrant policy collection.

Long-term persistence is explicit, selective, bounded, attributable, expirable, and deletable by stable ID. Memory never replaces current SQL or policy retrieval.

## Alternatives Considered

- One vector collection for conversations, policies, financial records, and memories.
- Automatically persist every conversation and tool result.
- Treat long-term memory as an authoritative operational database.

## Consequences

Authority and lifecycle rules remain understandable, deletion and retention are enforceable, and current facts stay in transactional systems. The tradeoff is additional configuration and coordination across distinct storage responsibilities.
