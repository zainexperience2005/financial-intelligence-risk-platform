"""Observability data models for trace metadata, correlation, and configuration."""

from typing import Any

from pydantic import BaseModel, Field

from kit.security.pii import mask_mapping
from kit.security.redaction import redact_mapping


def sanitize_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """Remove credential secrets and classified PII before tracing."""
    return mask_mapping(redact_mapping(data))


class TraceMetadata(BaseModel):
    """Correlation and context metadata for distributed AI and service traces."""

    request_id: str | None = None
    thread_id: str | None = None
    component: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_runnable_config(
        self,
        *,
        run_name: str | None = None,
    ) -> dict[str, Any]:
        """Convert trace metadata to a sanitized runnable configuration."""
        safe_meta = sanitize_metadata(self.metadata)
        if self.request_id:
            safe_meta["request_id"] = self.request_id
        if self.thread_id:
            safe_meta["thread_id"] = self.thread_id
        if self.component:
            safe_meta["component"] = self.component

        active_tags = list(self.tags)
        if self.component and self.component not in active_tags:
            active_tags.append(self.component)
        if self.request_id and f"request:{self.request_id}" not in active_tags:
            active_tags.append(f"request:{self.request_id}")

        cfg: dict[str, Any] = {
            "tags": active_tags,
            "metadata": safe_meta,
        }

        if self.thread_id:
            cfg["configurable"] = {"thread_id": self.thread_id}

        if run_name:
            cfg["run_name"] = run_name

        return cfg
