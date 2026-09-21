from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from kit.tools.result import ToolResult

InputT = TypeVar(
    "InputT",
    bound=BaseModel,
)


class BaseTool(ABC, Generic[InputT]):
    name: str
    description: str
    input_schema: type[InputT]

    @abstractmethod
    def execute(
        self,
        input_data: InputT,
    ) -> ToolResult:
        """Execute the tool."""
        raise NotImplementedError
