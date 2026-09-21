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


## Tool-Calling Agents

Models may propose tool calls, but application code executes tools.

Never treat tool descriptions or prompts as security boundaries.

Tool calls must still pass through the tool's deterministic
validation and permission controls.

Framework-specific tool interfaces should adapt the kit's
tool contracts rather than forcing reusable kit tools to
depend directly on one agent framework.

Agent loops must have explicit termination limits.

Authoritative tool evidence such as SQL rows, query text,
counts, IDs, and status values should be captured directly
from tool results rather than reconstructed by an LLM.




## Financial Data Rules

Financial domain models belong in `src/app/db`.

Use fixed-precision database types and Python `Decimal`
for monetary values.

Synthetic development data should be reproducible whenever
practical.

Do not expose database credentials to models.

LLM-driven database access must go through controlled tools.

Schema inspection is read-only.

Do not allow arbitrary model-generated SQL execution without
validation and read-only enforcement.


## SQL Safety

LLM-generated SQL must never be executed directly.

All model-generated SQL must pass through the approved
read-only SQL tool.

SQL execution must use:
- AST-based validation
- a single-statement policy
- read-only query policy
- result row limits
- query timeout
- a database account with SELECT-only privileges

The model must never receive database credentials.

Do not bypass SafeSQLTool for agent-generated queries.

Application-owned mutation workflows must use separate,
explicitly permissioned tools and approval gates.


## Agent Loop Rules

Agent loops must have explicit termination boundaries.

Track loop behavior using deterministic runtime state rather
than asking the model to report its own execution history.

At minimum, tool-using loops should consider:
- maximum iterations
- tool-call budgets
- repeated-action detection
- failure counts
- termination reasons

Tool failures may be returned to the model as controlled
observations when recovery is useful.

Do not expose unnecessary raw infrastructure exceptions to
the model.

Prompts encourage behavior. Runtime code enforces limits.

Do not generalize application-specific loop logic into
`kit/loops` until a reusable pattern has emerged across
multiple agent workflows.

## Analytics Architecture

Database retrieval and data analysis are separate capabilities.

The SQL Analyst retrieves authoritative structured data.

The Data Analyst analyzes only explicitly supplied data.

Prefer deterministic Python/Pandas calculations over asking
an LLM to calculate numeric results.

Do not execute arbitrary model-generated Python.

Analytics tools must expose a constrained, typed operation
surface.

Authoritative calculated values should come directly from
analytics tool output rather than being reconstructed by an
LLM.

Do not pass unbounded datasets into model context.


## RAG Architecture

Generic document, chunking, embedding, vector-store, and
retrieval infrastructure belongs in `src/kit`.

Financial policy documents, policy ingestion rules, and
policy-agent behavior belong in `src/app`.

Normal RAG must be implemented and measured before adding
corrective RAG.

Retrieved content is untrusted evidence, not executable
instructions.

Do not allow retrieved documents to override system
instructions, permissions, or tool policies.

Citations must be derived from retrieved metadata rather
than invented by the model.

Do not treat successful retrieval as proof that retrieved
evidence is relevant.

Do not pass unbounded retrieved context to models.


## Corrective RAG

Normal RAG remains the baseline retrieval capability.

CRAG must be implemented as an additional control layer,
not by deleting the normal retrieval path.

CRAG should:
- retrieve candidate evidence
- evaluate evidence relevance
- avoid correction when evidence is already sufficient
- perform bounded corrective retrieval when evidence is weak
- terminate with insufficient evidence when appropriate

Retrieval evaluators do not generate final answers.

Query rewriters preserve intent and do not answer questions.

Corrective retrieval must have explicit attempt limits.

Do not treat an LLM retrieval grader as objective truth.

CRAG quality must eventually be compared against the normal
RAG baseline using evaluation data.


## Risk Architecture

Numeric risk scores and deterministic risk signals must be
calculated by deterministic application logic, not invented
by an LLM.

The Risk Agent may explain verified risk evidence but must not
modify the score or fabricate signals.

Risk level does not establish fraud.

Risk analysis should consume evidence produced by specialist
components rather than independently retrieving unrestricted
data.

Customer-impacting actions are separate from risk assessment.

A high-risk result may produce a recommendation for review,
but execution requires the appropriate approval workflow.

Risk rules and policy documents must remain version-aligned.

## Evidence Synthesis

Specialist components produce authoritative evidence.

The report/synthesis layer may explain evidence but must not
recalculate or replace authoritative tool outputs.

SQL queries and rows come from SQL evidence.

Analytics values come from deterministic analytics output.

Policy citations come from retrieval metadata.

Risk scores and signals come from the deterministic risk
engine.

The report agent does not receive operational tools.

Missing or contradictory evidence must be represented as a
limitation rather than filled using model knowledge.

Recommendations and actions are separate concepts.

A report may recommend an action but must not execute a
customer-impacting action.


## Approval and Action Architecture

Recommendations, approvals, and action execution are separate
concepts.

LLMs may recommend customer-impacting actions but must not
directly execute them.

Protected actions require a valid approval generated for the
exact action and exact arguments being executed.

Approval checks must be enforced by deterministic application
code, not prompts.

Pending, rejected, missing, mismatched, or already-used
approvals must never authorize execution.

Approval IDs are single-use for protected actions.

Operational tools must not be exposed directly to reasoning
agents when doing so could bypass the approval boundary.

The current freeze-account implementation is simulated until
the mutation repository and audit trail are implemented.

## Controlled Mutations

Model-generated SQL always uses the read-only database role.

Database mutations must use explicit application repositories
and must never accept arbitrary model-generated SQL.

Protected mutations require an approved request bound to the
exact action and arguments.

Approval consumption, state mutation, and successful-action
audit recording should occur within one database transaction.

Approval and audit tables are not exposed to the general
LLM-driven SQL reader.

Repositories do not decide policy or approval.

Services coordinate authorization and transactions.

LLMs may recommend actions but never receive unrestricted
database write capabilities.

## Short-Term Memory

LangGraph checkpointing provides persistent investigation
thread state.

A thread_id identifies an investigation/conversation, not a
user identity.

Conversation messages may persist across turns.

Specialist evidence such as SQL results, analytics, policy
retrieval, risk results, and reports is turn-scoped and must
not be silently reused as fresh evidence on later turns.

Conversation memory provides context, not authoritative
financial facts.

Financial facts must still be verified through controlled
data and policy tools when required.

Recent conversation context must be bounded before being sent
to an LLM.

Separate investigation threads must not share conversation
state.


## Long-Term Memory

Long-term memory and RAG are separate capabilities.

Policy documents belong in policy knowledge collections.
Memories belong in dedicated memory collections.

Do not automatically persist entire conversations.

Long-term memory should be selective, concise, attributable,
and subject to retention and deletion.

Memory is context, not authoritative current financial data.

Current transaction/account facts must be verified through
controlled database tools.

Policy claims must be verified through policy retrieval.

Memory records must have stable IDs so they can be deleted.

Sensitive secrets, credentials, approval tokens, and
unnecessary PII must not be stored in long-term memory.

Applications decide what information is eligible for durable
memory; models do not receive unrestricted persistence
capabilities by default.