"""Component evaluation runner for deterministic transaction risk scoring."""

import json
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from typing import Any

from app.evaluation.scorers import score_risk_assessment
from app.risk.engine import assess_transaction_risk

DATASET_PATH = Path("evals/datasets/financial_golden.json")
REPORT_PATH = Path("evals/reports/risk-eval.json")


def run_risk_evaluation() -> dict[str, Any]:
    """Run deterministic risk evaluation against golden test cases."""
    raw = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    risk_cases = [c for c in raw if c.get("category") == "risk"]

    results = []
    total_checks = 0
    passed_checks = 0

    for case in risk_cases:
        tx = case["input"]["transaction"]
        started_at = perf_counter()
        actual = assess_transaction_risk(
            amount=Decimal(str(tx["amount"])),
            status=str(tx["status"]),
            failure_reason=tx.get("failure_reason"),
            destination_country=tx.get("destination_country"),
            customer_country=case["input"]["customer_country"],
        )

        latency_seconds = perf_counter() - started_at

        scores = score_risk_assessment(
            actual=actual,
            expected_score=case["expected"]["risk_score"],
            expected_level=case["expected"]["risk_level"],
            expected_signals=case["expected"].get("expected_signals"),
        )

        for s in scores:
            total_checks += 1
            if s.passed:
                passed_checks += 1

        results.append(
            {
                "case_id": case["case_id"],
                "description": case.get("metadata", {}).get("description"),
                "actual": {
                    "score": actual.score,
                    "level": actual.level,
                    "signals": [sig.code for sig in actual.signals],
                },
                "expected": case["expected"],
                "latency_seconds": latency_seconds,
                "scores": [s.model_dump() for s in scores],
                "all_passed": all(s.passed for s in scores),
            }
        )

    summary = {
        "dataset": str(DATASET_PATH),
        "total_cases": len(risk_cases),
        "passed_cases": sum(1 for r in results if r["all_passed"]),
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "latency_seconds": sum(result["latency_seconds"] for result in results),
        "accuracy_pct": round((passed_checks / total_checks) * 100, 2)
        if total_checks > 0
        else 0.0,
        "results": results,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


def main() -> None:
    summary = run_risk_evaluation()
    passed_cases = summary["passed_cases"]
    total_cases = summary["total_cases"]
    accuracy = summary["accuracy_pct"]
    passed_checks = summary["passed_checks"]
    total_checks = summary["total_checks"]

    print(f"Risk Evaluation Finished: {passed_cases}/{total_cases} cases passed.")
    print(f"Check Accuracy: {accuracy}% ({passed_checks}/{total_checks})")
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
