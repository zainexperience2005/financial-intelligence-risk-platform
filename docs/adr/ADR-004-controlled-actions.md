# ADR-004: Approval-Controlled Customer Actions

## Status

Accepted

## Context

Financial investigations may recommend customer-impacting actions such as freezing an account. A model recommendation is neither authorization nor evidence that an action occurred. Approval replay, argument substitution, races, and incomplete auditing must be prevented deterministically.

## Decision

Separate recommendation, approval, and execution:

```text
recommend -> request approval -> human decision -> exact action and arguments
          -> row lock -> execute once -> authoritative audit
```

Execution locks the approval record, requires approved status, compares the exact action and account arguments, and consumes a single-use approval. Successful mutation, approval consumption, and success audit are one transaction. A denied action rolls back first and then records a sanitized denial event in an independent transaction; failure to persist that denial leaves the action denied.

## Alternatives Considered

- Expose `freeze_account` directly to the LLM.
- Treat a recommendation as implicit approval.
- Validate only the approval ID without binding action arguments.
- Record denials inside the transaction that is rolled back.

## Consequences

Customer-impacting actions have explicit human authority, replay and substitution defenses, concurrency protection, and an authoritative audit trail. Execution requires more service and repository coordination, and denial auditing needs a separate reliable transaction.
