from unittest.mock import patch

import pytest
from langchain_openai import ChatOpenAI

from kit.config.settings import Settings
from kit.llms.config import LLMConfig
from kit.llms.factory import create_chat_model, get_llm_config


def test_llm_config_defaults():
    config = LLMConfig()
    assert config.provider == "openai"
    assert config.model == "gpt-4.1-mini"
    assert config.temperature == 0.0
    assert config.max_tokens is None
    assert config.api_key is None


def test_get_llm_config_maps_settings():
    mock_settings = Settings(
        llm_provider="openai",
        llm_model="gpt-4.1-mini",
        llm_temperature=0.7,
        llm_max_tokens=100,
        openai_api_key="test-api-key",
    )

    with patch("kit.llms.factory.get_settings", return_value=mock_settings):
        config = get_llm_config()
        assert config.provider == "openai"
        assert config.model == "gpt-4.1-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 100
        assert config.api_key == "test-api-key"


def test_create_chat_model_passes_api_key():
    config = LLMConfig(
        provider="openai",
        model="gpt-4.1-mini",
        temperature=0.2,
        max_tokens=50,
        api_key="test-openai-key",
    )

    model = create_chat_model(config)
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-4.1-mini"
    assert model.temperature == 0.2
    assert model.max_tokens == 50
    assert model.openai_api_key.get_secret_value() == "test-openai-key"


def test_create_chat_model_unsupported_provider():
    config = LLMConfig.model_construct(provider="unsupported")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_chat_model(config)
