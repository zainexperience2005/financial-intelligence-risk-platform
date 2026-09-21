import sys
from pathlib import Path

# Add src directory to sys.path for standalone script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from app.agents.sql_analyst import (
    run_sql_analyst,
)


def main() -> None:
    question = (
        "For transaction TX-1006, find the customer's "
        "name, account ID, transaction amount, status, "
        "and destination country."
    )

    result = run_sql_analyst(
        question
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()