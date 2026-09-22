# Quality Gates

Tests establish software correctness and safety invariants. Evaluations measure
the quality, grounding, usefulness, latency, and cost of AI behavior. These are
reported separately; a probabilistic quality score never compensates for a
failed security invariant.

## Quality matrix

| Gate | PR | Release | Production |
| --- | ---: | ---: | ---: |
| Ruff | Yes | Yes | - |
| Unit tests | Yes | Yes | - |
| Security tests | Yes | Yes | - |
| Golden dataset validation | Yes | Yes | - |
| Deterministic evals | Yes | Yes | - |
| Migration test | Yes | Yes | - |
| DB integration | Yes | Yes | - |
| Docker build | Yes | Yes | - |
| LLM eval | Optional/manual | Yes | - |
| E2E | Optional | Yes | - |
| Clean-clone verification | - | Yes | - |
| Health smoke | - | - | Yes |
| Readiness smoke | - | - | Yes |

## Suites and execution

| Layer | Purpose | Command | Normal schedule |
| --- | --- | --- | --- |
| Unit | Fast, isolated deterministic correctness | `make unit` | Every commit and PR |
| Security | Binary safety and authorization invariants | `make security` | Every commit, PR, and release |
| Integration | Real component and infrastructure boundaries | `make integration` | Infrastructure CI and release |
| Deterministic evaluation | Exact golden-case behavior | `make eval` | Every PR and release |
| LLM evaluation | Semantic grounding and model behavior | `make llm-eval` | Manual/scheduled and release |
| E2E | Full workflow behavior | `make e2e` | Intentional and release |
| Production smoke | Liveness/readiness without mutation | `/health`, `/ready` | Post-deploy |

Unit tests must not use OpenAI, Qdrant, PostgreSQL, or the internet. Integration
tests are selected with the `integration` marker. Paid/provider-backed tests use
the `llm` marker. Full workflows use `e2e`; MCP boundary tests use `mcp`.

The golden source of truth is `evals/datasets/financial_golden.json`. Dataset
schema, minimum size, and unique case IDs are validated before experiments.
Deterministic expectations such as routes, risk scores, policy sources, chart
types, and approval denials use programmatic scorers. LLM judges are reserved
for semantic properties and must be checked against known positive and negative
examples.

Evaluation reports must keep capability metrics separate: planner routing, SQL
correctness, analytics numeric consistency, chart data consistency, policy
source recall, CRAG grounding/refusal, risk correctness, report groundedness,
approval bypass count, latency, token use, and cost. Unknown pricing is recorded
as `null`, never zero. Establish measured baselines before setting probabilistic
thresholds.

Experiment artifacts belong under `evals/reports/`. Baselines should be retained;
new experiment filenames should eventually include date, Git SHA, model, and
dataset version. Normal RAG and CRAG comparisons must use the same policy cases
and report retrieval attempts, source recall, refusal behavior, latency, tokens,
and estimated cost.

## Release blockers

The following are unconditional release blockers:

- unit, security, migration, integration, or Docker build failure;
- malformed golden evaluation data;
- deterministic evaluation regression outside an explicitly accepted threshold;
- approval bypass or replay;
- unsafe SQL execution or failure of the database read-only boundary;
- a fabricated successful action in a deterministic workflow.

Probabilistic LLM metrics become release gates only after a documented baseline
and justified threshold exist.

## Release verification

Run `make quality`, `make integration`, and `make eval`, then intentionally run
`make llm-eval` and `make e2e` with their required credentials and services.
Build the container and complete the clean-clone checklist before release. After
deployment, call only the safe health and readiness probes.