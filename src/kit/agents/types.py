from enum import StrEnum


class AgentArchitecture(StrEnum):
    REACT = "react"
    PLANNER_EXECUTOR = "planner_executor"
    HYBRID = "hybrid"
