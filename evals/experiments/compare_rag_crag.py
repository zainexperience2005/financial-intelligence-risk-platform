"""Compare normal policy RAG with bounded corrective RAG on the same cases."""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for import_path in (ROOT, SRC):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from app.tools.corrective_policy_retrieval import CorrectivePolicyRetrievalTool
from app.tools.policy_retrieval import PolicyRetrievalTool
from evals.scorers.policy import expected_source_files

DATASET_PATH = ROOT / "evals" / "datasets" / "financial_golden.json"
REPORT_DIR = ROOT / "evals" / "reports"


def _git_sha() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _load_cases() -> list[dict[str, Any]]:
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    return [item for item in cases if item["category"] in {"policy", "unsupported"}]


def _sources(chunks: list[dict[str, Any]]) -> set[str]:
    return {str(chunk.get("source")) for chunk in chunks if chunk.get("source")}


def _run_normal(question: str) -> dict[str, Any]:
    result = PolicyRetrievalTool().run({"query": question, "k": 4})
    chunks = result.data if result.success and isinstance(result.data, list) else []
    return {
        "success": result.success,
        "answerable": bool(chunks),
        "chunks": chunks,
        "retrieval_attempts": 1,
        "correction_used": False,
        "error": str(result.error) if result.error else None,
    }


def _run_crag(question: str) -> dict[str, Any]:
    result = CorrectivePolicyRetrievalTool().run({"query": question, "k": 4})
    data = result.data if result.success and isinstance(result.data, dict) else {}
    return {
        "success": result.success,
        "answerable": bool(data.get("answerable")),
        "chunks": data.get("chunks", []),
        "retrieval_attempts": data.get("retrieval_attempts"),
        "correction_used": data.get("correction_used"),
        "relevance": data.get("relevance"),
        "error": str(result.error) if result.error else None,
    }


def _score(
    case: dict[str, Any], mode: str, actual: dict[str, Any], latency: float
) -> dict[str, Any]:
    expected = case["expected"]
    required_sources = expected_source_files(expected)
    actual_sources = _sources(actual["chunks"])
    source_correct = (
        required_sources.issubset(actual_sources) if required_sources else None
    )
    refusal_correct = None
    if case["category"] == "unsupported" and expected.get("grounded") is False:
        refusal_correct = not actual["answerable"]
    checks = [value for value in (source_correct, refusal_correct) if value is not None]
    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "mode": mode,
        "passed": bool(checks) and all(checks),
        "source_correct": source_correct,
        "unsupported_refusal_correct": refusal_correct,
        "grounding_correct": (
            refusal_correct if refusal_correct is not None else source_correct
        ),
        "expected_sources": sorted(required_sources),
        "actual_sources": sorted(actual_sources),
        "answerable": actual["answerable"],
        "retrieval_attempts": actual["retrieval_attempts"],
        "correction_used": actual["correction_used"],
        "relevance": actual.get("relevance"),
        "latency_seconds": latency,
        "input_tokens": None,
        "output_tokens": None,
        "estimated_cost_usd": None,
        "error": actual["error"],
    }


def _rate(values: list[bool]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values) * 100, 2)


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [item["latency_seconds"] for item in results]
    attempts = [
        item["retrieval_attempts"]
        for item in results
        if item["retrieval_attempts"] is not None
    ]
    source_checks = [
        item["source_correct"] for item in results if item["source_correct"] is not None
    ]
    grounding_checks = [
        item["grounding_correct"]
        for item in results
        if item["grounding_correct"] is not None
    ]
    refusal_checks = [
        item["unsupported_refusal_correct"]
        for item in results
        if item["unsupported_refusal_correct"] is not None
    ]
    return {
        "passed": sum(item["passed"] for item in results),
        "total": len(results),
        "pass_rate_pct": round(
            sum(item["passed"] for item in results) / len(results) * 100, 2
        ),
        "source_recall_pct": _rate(source_checks),
        "grounding_pct": _rate(grounding_checks),
        "unsupported_refusal_pct": _rate(refusal_checks),
        "average_retrieval_attempts": statistics.fmean(attempts) if attempts else None,
        "average_latency_seconds": statistics.fmean(latencies),
        "median_latency_seconds": statistics.median(latencies),
        "token_usage": None,
        "estimated_cost_usd": None,
    }


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Normal RAG vs Corrective RAG",
        "",
        f"- Dataset cases: **{report['case_count']}**",
        f"- Git SHA: `{report['git_sha'] or 'unknown'}`",
        "- Token and cost telemetry: **unavailable**",
        "",
        "| Mode | Source recall | Grounding | Unsupported refusals | "
        "Avg attempts | Avg latency |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode in ("normal_rag", "crag"):
        item = report["summary"][mode]
        lines.append(
            f"| {mode} | {item['source_recall_pct']}% | "
            f"{item['grounding_pct']}% | {item['unsupported_refusal_pct']}% | "
            f"{item['average_retrieval_attempts']:.2f} | "
            f"{item['average_latency_seconds']:.3f}s |"
        )
    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Mode | Pass | Sources | Answerable |",
            "|---|---|---|---|---|",
        ]
    )
    for item in report["results"]:
        lines.append(
            f"| {item['case_id']} | {item['mode']} | {item['passed']} | "
            f"{', '.join(item['actual_sources']) or 'none'} | {item['answerable']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    cases = _load_cases()
    results: list[dict[str, Any]] = []
    for case in cases:
        question = str(case["input"]["question"])
        for mode, runner in (("normal_rag", _run_normal), ("crag", _run_crag)):
            started = perf_counter()
            actual = runner(question)
            scored = _score(case, mode, actual, perf_counter() - started)
            results.append(scored)
            print(
                f"{case['case_id']} {mode}: {'PASS' if scored['passed'] else 'FAIL'}",
                flush=True,
            )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_sha": _git_sha(),
        "dataset_version": "1.0",
        "case_count": len(cases),
        "summary": {
            mode: _summarize([item for item in results if item["mode"] == mode])
            for mode in ("normal_rag", "crag")
        },
        "results": results,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sha = report["git_sha"] or "unknown"
    stem = f"{datetime.now(UTC).date().isoformat()}_rag_crag_{sha}"
    json_path = REPORT_DIR / f"{stem}.json"
    md_path = REPORT_DIR / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _write_markdown(md_path, report)
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
