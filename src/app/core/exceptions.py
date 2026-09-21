"""Core application domain exceptions."""


class ApplicationError(Exception):
    """Base application exception for controlled domain errors."""

    code = "application_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvestigationError(ApplicationError):
    """Raised when an investigation request cannot be completed."""

    code = "investigation_failed"


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource does not exist."""

    code = "resource_not_found"


class ActionNotAllowedError(ApplicationError):
    """Raised when an operation or action violates domain permissions/state."""

    code = "action_not_allowed"


class ConflictError(ApplicationError):
    """Raised when an action conflicts with existing state (e.g. already decided)."""

    code = "conflict"
