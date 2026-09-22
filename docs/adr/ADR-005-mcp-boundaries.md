# ADR-005: MCP Capability Boundaries

## Status

Accepted

## Context

MCP provides a standard interface for tools, resources, and prompts, but protocol exposure can tempt implementations to duplicate business rules or bypass existing validation and authorization.

## Decision

MCP exposes selected capabilities but does not own business rules or grant authority. Application MCP handlers delegate to existing SafeSQL, risk, schema, and policy implementations. Generic discovery and client adaptation belong in `src/kit`; financial MCP contracts belong in `src/app`. Customer-impacting mutations remain behind the same approval boundary and are not exposed as unrestricted tools.

## Alternatives Considered

- Reimplement SQL validation and risk scoring inside MCP handlers.
- Expose every internal function as an MCP tool.
- Treat MCP clients as trusted and bypass application authorization.

## Consequences

REST, LangGraph, and MCP can reuse consistent controls, and the kit remains reusable across domains. The available MCP surface must be curated and adapters must preserve supported schema semantics and controlled failures.
