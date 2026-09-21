from app.agents.policy_agent import (
    run_policy_agent,
)


def main() -> None:
    result = run_policy_agent(
        "What policy applies to a PKR 475,000 "
        "international transfer that failed because "
        "of risk review?"
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
