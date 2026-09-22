"""Keep automated tests independent of local credentials and live services."""

import os

import pytest

from kit.config import get_settings

# Set deterministic defaults before test collection imports application modules.
_TEST_DEFAULTS = {
    "APP_ENV": "test",
    "ENVIRONMENT": "test",
    "DEBUG": "false",
    "DATABASE_URL": "sqlite://",
    "READ_ONLY_DATABASE_URL": "sqlite://",
    "CHECKPOINT_DATABASE_URL": "sqlite://",
    "OPENAI_API_KEY": "test-key-not-a-secret",
    "LLM_PROVIDER": "openai",
    "LLM_MODEL": "test-model",
    "LLM_TEMPERATURE": "0",
    "EMBEDDING_PROVIDER": "openai",
    "EMBEDDING_MODEL": "test-embedding",
}
if os.getenv("PYTEST_USE_EXTERNAL_SERVICES") == "1":
    for name, value in _TEST_DEFAULTS.items():
        os.environ.setdefault(name, value)
else:
    os.environ.update(_TEST_DEFAULTS)
get_settings.cache_clear()


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Apply suite markers from directory boundaries during gradual migration."""
    for item in items:
        path_parts = set(item.path.parts)
        if "integration" in path_parts:
            item.add_marker(pytest.mark.integration)
        if "e2e" in path_parts:
            item.add_marker(pytest.mark.e2e)
        if "mcp" in path_parts:
            item.add_marker(pytest.mark.mcp)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
