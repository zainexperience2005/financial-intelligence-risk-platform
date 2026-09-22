# Financial Intelligence & Risk Platform — Threat Model

## Security Objectives

The system must prevent:

1. unauthorized database mutations
2. approval bypass
3. approval replay
4. approval argument substitution
5. unsafe model-generated SQL
6. prompt injection gaining instruction authority
7. unauthorized MCP capability access
8. leakage of credentials or unnecessary PII
9. uncontrolled agent loops and spend
10. fabricated claims of executed financial actions

---

## Trust Boundaries

### Untrusted (Zero Authority)
- user prompts and query text
- retrieved policy chunks and external documents
- tool outputs and API observations
- MCP external responses
- model-generated SQL statements
- model-generated action recommendations and narrative claims

### Trusted Only After Deterministic Validation
- AST-validated, SELECT-only SQL queries with forced row limits
- deterministic risk engine calculations
- verified approval state records (`approved`)
- exact action arguments matching approved payloads

### Highly Trusted (Application Execution Core)
- application database write connection
- controlled action executor and approval transition manager
- immutable audit repository
- secrets, environment configuration, and container least-privilege users

---

## Primary Security Guardrails

### Guardrail 1: Safe SQL & Database Isolation
- **Primary Control**: AST-based parsing and validation via `sqlglot`. Only single-statement `SELECT` / `UNION` queries are permitted. `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, and subquery mutations are rejected before database dispatch.
- **Secondary Control**: Dedicated read-only database role (`financial_reader`) possessing strictly `SELECT` permissions on business tables, preventing mutations even if AST validation were bypassed.

### Guardrail 2: Controlled Mutations & Human-in-the-Loop Approvals
- **Approval Gate**: Customer-impacting actions (e.g. `freeze_account`) require explicit human review resulting in a verified `approved` database state.
- **Exact Argument Binding**: The approval record is strictly bound to the exact action name and exact argument dictionary. An approval for `ACC-1001` cannot be executed for `ACC-9999`.
- **Single-Use & Replay Protection**: Approvals transition atomically from `approved` to `executed` with row-level locking (`SELECT ... FOR UPDATE`), permanently preventing sequential or concurrent replay.
- **Atomic Transaction & Audit**: Mutation, approval state transition, and audit event creation occur within a single database transaction. Denied attempts are captured in separate audit logs.

### Guardrail 3: Agent Resource & Loop Controls
- **Multi-Dimensional Budgets**: Deterministic runtime limits for maximum reasoning iterations, tool calls, failure counts, repeated action signatures, token consumption, and cost in USD.
- **Pre-Execution Guards**: Repeated identical actions are blocked before execution (`StopReason.REPEATED_ACTION`).
- **Context Bounding**: Priority-based context budgeting prevents token flooding and denial-of-wallet attacks.

### Guardrail 4: RAG & Prompt Injection Boundary
- Retrieved policy documents and tool outputs are treated strictly as untrusted evidence/data, not system instructions.
- The LLM has zero autonomous mutation tools; prompt injections instructing the agent to execute actions fail due to absence of operational execution tools.

### Guardrail 5: MCP Capability Allowlisting
- Dangerous mutations (such as `freeze_account`) are not exposed through the MCP protocol.
- MCP data retrieval tools delegate directly to `SafeSQLTool` rather than executing unvalidated SQL.

### Guardrail 6: Credential & PII Redaction
- Automatic recursive scrubbing of keys containing `api_key`, `token`, `password`, `secret`, `database_url`, and credentials from logs, trace metadata, and tool error messages.

---

## Threat Matrix

| Threat | Primary Control | Secondary Control | Test Suite |
|---|---|---|---|
| **SQL Mutation** | AST validator (`sqlglot`) | Read-only DB role (`financial_reader`) | `tests/security/test_sql_attacks.py` |
| **Approval Bypass** | Approval status check (`approved`) | ActionService permission enforcement | `tests/security/test_approval_bypass.py` |
| **Approval Replay** | Single-use `executed` state | Row-level locking (`FOR UPDATE`) | `tests/security/test_approval_replay.py` |
| **Argument Substitution** | Exact argument dictionary match | Single-use consumption & audit log | `tests/security/test_argument_substitution.py` |
| **Prompt Injection** | Untrusted data boundary in prompts | Complete lack of autonomous mutation tools | `tests/security/test_prompt_injection.py` |
| **Infinite Agent Loop** | `LoopController` repetition guard | LangGraph recursion limits | `tests/security/test_tool_abuse.py` |
| **Cost & Token Exhaustion** | Fail-closed token & cost budget ceilings | Hard iteration and tool budgets | `tests/security/test_resource_limits.py` |
| **Context Flooding** | `ContextBuilder` priority degradation | Request body size limits & row limits | `tests/security/test_resource_limits.py` |
| **MCP Capability Abuse** | Strict tool allowlist (no mutation tools) | Delegation to internal SafeSQL boundary | `tests/security/test_mcp_security.py` |
| **Secret Leakage** | `redact_mapping` & `sanitize_metadata` | Trace minimization & non-root container | `tests/security/test_secret_leakage.py` |
| **Fabricated Action Claims** | Semantic `GroundingJudge` | Authoritative PostgreSQL audit trail | `tests/unit/app/evaluation/test_judges.py` |