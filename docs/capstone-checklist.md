# Capstone Checklist

## Evaluation and Release Status

| Step | Status | Evidence |
|---|---|---|
| 40J — PII masking | Complete | Model-boundary masking and security regressions are present. |
| 40K — Immutable audit | Complete | Approval/action auditing is covered by deterministic tests. |
| 40L — LangSmith verification | Complete | Observability remains optional for local evaluation. |
| 40M — Final 24-case evaluation | Evaluated; release blocked | Baseline executed on 2026-09-22; 17/24 passed and one hard gate failed. |
| 40N — Final release verification | Pending | Do not begin release verification until the failures below are addressed. |

## Step 40M Actual Baseline

- Git SHA: `046cad7`
- Dataset version: `1.0`
- Retrieval mode: `crag`
- Overall: **17/24 (70.83%)**
- SQL: **2/4**
- Analytics: **0/4**
- Policy: **4/4**
- Risk: **4/4**
- Unsupported/adversarial: **3/4**
- Safety/actions: **4/4**
- Average latency: **6.738 s**
- Median latency: **7.835 s**
- p95 latency: **10.419 s**
- Token/cost coverage: **0/24**; provider usage was unavailable and is recorded as unknown, not zero.
- Hard gates: **FAIL** — `unsupported_policy_fabrication=1`; all other hard-gate counters are zero.
- Release candidate: **NO**

The failure clusters are SQL tool-loop/schema evidence failures (which cascade into analytics), one analytics planning miss, and one adversarial automatic-freeze policy fabrication. The baseline report must remain intact while these layers are investigated.

## Normal RAG vs CRAG

| Metric | Normal RAG | CRAG |
|---|---:|---:|
| Source recall | 100.0% | 100.0% |
| Grounding | 57.14% | 100.0% |
| Unsupported refusals | 0.0% | 100.0% |
| Average retrieval attempts | 1.00 | 1.50 |
| Average latency | 0.812 s | 3.650 s |
| Passed cases | 4/8 | 7/8 |
| Token/cost | unknown | unknown |

CRAG improved grounding and unsupported refusal behavior on this small corpus, at higher retrieval latency and with more attempts. This 24-case set is now a baseline and should not be repeatedly prompt-tuned as the only evaluation set; add held-out release cases.

## Deterministic Gates Observed Before Baseline

- Ruff lint and scoped format checks: pass
- Unit tests: **207 passed**
- Security tests: **56 passed**
- Integration marker: **27 passed, 5 failed, 9 skipped**. The five failures are stale denial-contract assertions that expect returned denial results while the current fail-closed action API raises `ActionNotAllowedError`.

## Artifacts

- `evals/reports/2026-09-22_full_eval_046cad7_crag_baseline.json`
- `evals/reports/2026-09-22_full_eval_046cad7_crag_baseline.md`
- `evals/reports/2026-09-22_rag_crag_046cad7.json`
- `evals/reports/2026-09-22_rag_crag_046cad7.md`