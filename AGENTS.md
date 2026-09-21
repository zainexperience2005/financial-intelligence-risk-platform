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

## Prompt Rules

Generic prompt-building utilities belong in `src/kit/prompts`.

Domain-specific prompts belong in `src/app/prompts`.

Do not place business-specific instructions inside the kit.

## Structured Output

Prefer Pydantic structured outputs when model results are consumed
by application logic.

Do not parse free-form LLM text when a typed schema can represent
the required result.


## LangGraph Rules

Financial/domain workflows belong in `src/app/graphs`.

Generic reusable LangGraph infrastructure belongs in
`src/kit/graphs`.

Do not put business-specific graph nodes in the kit.

Nodes should:
- accept explicit state
- return explicit state updates
- remain small and focused
- avoid hidden global state
- use typed state where practical

Prefer deterministic Python nodes when LLM reasoning is
not required.


## Routing Rules

Prefer deterministic routing when the required routing signal
already exists in structured state.

Do not add an additional LLM call when normal Python can make
the decision reliably.

Routers should:
- inspect explicit graph state
- return a small typed set of route names
- avoid side effects
- avoid modifying state

Keep routing separate from business operations where practical.


## Planning Rules

The planner determines WHAT work is required.

The planner must not perform the actual work.

Planning output should be structured and validated.

Prefer capability flags or typed task descriptions over
free-form planning prose when downstream graph routing depends
on the result.

Application-specific planning logic belongs in `src/app`.

Do not place finance-specific planning rules in `src/kit`.

Graph routing should consume structured planner output rather
than parsing natural-language planning text.


## Tool Architecture

Reusable tool infrastructure belongs in `src/kit/tools`.

Domain-specific tool implementations belong in `src/app/tools`.

Tools must:
- have a clear name
- have a clear description
- use typed input schemas
- return predictable results
- expose controlled failures
- be independently testable

Agents must not directly access databases or external APIs
when an appropriate tool boundary exists.

Before creating a new tool:
1. Search the existing tool registry.
2. Reuse an existing capability where possible.
3. Determine whether the tool is generic or domain-specific.
4. Add reusable infrastructure to kit only when justified.

Do not use an LLM for deterministic work that normal Python
or a dedicated tool can perform reliably.