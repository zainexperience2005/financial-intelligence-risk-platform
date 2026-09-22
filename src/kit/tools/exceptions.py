"""Domain-independent tool execution exceptions."""


class ToolExecutionError(Exception):
    """Base exception for tool execution errors."""


class RetryableToolError(ToolExecutionError):
    """Exception raised when a tool failure is temporary and can safely be retried."""


class PermanentToolError(ToolExecutionError):
    """Exception raised when a tool failure is deterministic and permanent."""
