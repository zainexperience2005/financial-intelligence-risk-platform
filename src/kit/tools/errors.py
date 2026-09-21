class ToolError(Exception):
    """Base exception for tool execution errors."""


class ToolValidationError(ToolError):
    """Raised when tool input is invalid."""


class ToolExecutionError(ToolError):
    """Raised when a tool fails during execution."""


class ToolTimeoutError(ToolError):
    """Raised when a tool exceeds its execution timeout."""