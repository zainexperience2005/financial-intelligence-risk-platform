from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

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

    def run(self, input_data: Any = None) -> ToolResult:
        """Validate input and execute the tool."""
        if input_data is None:
            validated = self.input_schema.model_validate({})
        elif isinstance(input_data, self.input_schema):
            validated = input_data
        elif isinstance(input_data, dict):
            validated = self.input_schema.model_validate(input_data)
        else:
            validated = self.input_schema.model_validate(input_data)
        return self.execute(validated)
