"""Keep automated tests independent of local credentials and live services."""

import os

import pytest

from kit.config import get_settings

# Set deterministic defaults before test collection imports application modules.
os.environ.update(
    DATABASE_URL="sqlite://",
    READ_ONLY_DATABASE_URL="sqlite://",
    CHECKPOINT_DATABASE_URL="sqlite://",
    OPENAI_API_KEY="test-key-not-a-secret",
    LLM_PROVIDER="openai",
    LLM_MODEL="test-model",
    LLM_TEMPERATURE="0",
    EMBEDDING_PROVIDER="openai",
    EMBEDDING_MODEL="test-embedding",
)
get_settings.cache_clear()


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
