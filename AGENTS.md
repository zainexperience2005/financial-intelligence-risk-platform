# Coding Agent Instructions

## Repository Architecture

Read `ARCHITECTURE.md` before making architectural changes.

The repository contains:

- `src/kit`: reusable Agentic AI infrastructure
- `src/app`: Financial Intelligence & Risk Platform

## Dependency Direction

`app` may import from `kit`.

`kit` MUST NOT import from `app`.

## Before Writing New Infrastructure

1. Search `src/kit` for an existing capability.
2. Reuse existing kit components when possible.
3. Do not duplicate infrastructure inside `src/app`.
4. Put domain-specific financial logic inside `src/app`.
5. Add code to `src/kit` only when it is domain-independent.

## Development Rules

- Use typed Python.
- Use Pydantic for external data validation.
- Do not hard-code secrets.
- Add tests for reusable kit components.
- Prefer explicit code over hidden magic.
- Do not introduce a new dependency without justification.