"""Sync local version-controlled golden dataset to LangSmith."""

import json
import os
from pathlib import Path

from kit.evaluation.models import EvaluationCase

DATASET_PATH = Path("evals/datasets/financial_golden.json")
DATASET_NAME = "financial-intelligence-golden-v1"
DESCRIPTION = (
    "Golden evaluation dataset for Financial Intelligence & Risk Platform "
    "covering SQL, analytics, policy CRAG, deterministic risk, and safety gates."
)


def load_and_validate_cases() -> list[EvaluationCase]:
    """Load and validate all golden evaluation cases."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Golden dataset file not found at {DATASET_PATH}")

    raw_data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    cases = [EvaluationCase.model_validate(c) for c in raw_data]
    return cases


def sync_to_langsmith() -> None:
    """Synchronize golden cases to LangSmith dataset."""
    cases = load_and_validate_cases()
    print(f"Loaded {len(cases)} valid golden cases from {DATASET_PATH}")

    api_key = os.environ.get("LANGSMITH_API_KEY")
    if not api_key:
        print(
            "\n[NOTICE] LANGSMITH_API_KEY is not set.\n"
            "Skipping remote LangSmith synchronization.\n"
            f"All {len(cases)} local cases are validated and ready to sync "
            "when credentials are provided."
        )
        return

    try:
        import langsmith

        client = langsmith.Client(api_key=api_key)

        # Check if dataset already exists
        datasets = list(client.list_datasets(dataset_name=DATASET_NAME))
        if datasets:
            dataset = datasets[0]
            print(
                f"Found existing LangSmith dataset: {dataset.name} (id: {dataset.id})"
            )
        else:
            dataset = client.create_dataset(
                dataset_name=DATASET_NAME,
                description=DESCRIPTION,
            )
            print(f"Created new LangSmith dataset: {dataset.name} (id: {dataset.id})")

        # Sync cases
        existing_examples = {
            ex.metadata.get("case_id"): ex
            for ex in client.list_examples(dataset_id=dataset.id)
            if ex.metadata and ex.metadata.get("case_id")
        }

        created = 0
        updated = 0
        for case in cases:
            metadata = dict(case.metadata)
            metadata["case_id"] = case.case_id
            metadata["category"] = case.category

            if case.case_id in existing_examples:
                ex = existing_examples[case.case_id]
                client.update_example(
                    example_id=ex.id,
                    inputs=case.input,
                    outputs=case.expected,
                    metadata=metadata,
                )
                updated += 1
            else:
                client.create_example(
                    inputs=case.input,
                    outputs=case.expected,
                    dataset_id=dataset.id,
                    metadata=metadata,
                )
                created += 1

        print(
            f"Synchronization Complete: {created} created, {updated} updated "
            f"in dataset '{DATASET_NAME}'."
        )

    except Exception as exc:
        print(f"Failed to sync dataset to LangSmith: {exc}")


if __name__ == "__main__":
    sync_to_langsmith()
