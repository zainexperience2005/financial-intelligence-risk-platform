# Evaluation Suite

The golden dataset evaluates the Financial Intelligence & Risk Platform against deterministic synthetic data and synthetic financial policy documents.

The dataset is not intended to represent universal banking rules.

## Dataset Structure

The golden dataset is stored in [financial_golden.json](file:///d:/Agentic%20AI%20Projects/FDE%20Projects/financial-intelligence-risk-platform/evals/datasets/financial_golden.json) and comprises 24 representative test cases categorized across the system's operational boundaries:

| Category | Cases | Focus & Validation Scope |
|---|---|---|
| **SQL Investigation** | 4 | Known transaction lookups, status filtering, customer history, high-value searches, and conversational bypass |
| **Analytics** | 4 | Summaries, grouped sums, categorical breakdowns, and empty dataset edge cases |
| **Policy RAG / CRAG** | 4 | Threshold rules, international transfer checks, failure procedures, and human-in-the-loop restriction mandates |
| **Deterministic Risk** | 4 | Multi-signal combinations, high-value transfers, domestic transactions, and international failed scenarios |
| **Unsupported Evidence** | 4 | Out-of-domain queries (cryptocurrency, rewards) and non-existent database records |
| **Action Safety** | 4 | Pending approval rejection, exact argument verification, and single-use approval replay prevention |

## Scoring Principles

1. **Deterministic Properties Use Deterministic Scorers**:
   - Numeric properties (e.g. risk score points, row counts) and categorical labels (e.g. risk level, approval status) are scored with exact programmatic checks (`exact_match`, `numeric_match`).
   - LLM judges are never used when programmatic evaluation is possible.

2. **Source Recall vs. Grounding**:
   - Citation presence (`expected_sources`) measures source retrieval recall.
   - Grounding verifies whether claims are entailed by retrieved content and checks that out-of-domain inquiries report `grounded: false`.

3. **Safety Invariants vs. Quality Metrics**:
   - Safety invariants (e.g. approval bypass, argument substitution, write-through read-only SQL) are treated as non-negotiable hard gates.
   - A single safety failure fails the gate, regardless of average accuracy across quality metrics.

4. **Layered Evaluation**:
   - **Component Eval**: Direct testing of isolated deterministic components (e.g. `assess_transaction_risk`).
   - **Agent Eval**: Specialist agent performance (e.g. SQL retrieval, CRAG evaluator).
   - **Workflow Eval**: Hybrid LangGraph orchestration.
   - **End-to-End Eval**: Complete system response from user inquiry to formatted report.

## Running Evaluations

Run the complete 24-case workflow evaluation after deterministic quality gates pass:

```bash
make eval
```

Run the same policy and unsupported-evidence cases through normal RAG and CRAG:

```bash
make rag-crag-eval
```

Both commands write timestamped JSON and Markdown artifacts under `evals/reports/`. Provider token and cost fields remain `null` when the provider response path does not expose usage metadata; the reports never represent unknown cost as zero.

The smaller deterministic risk-only experiment remains available as `make risk-eval`.
