from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from kit.config import get_settings
from kit.llms.config import LLMConfig


def get_llm_config() -> LLMConfig:
    settings = get_settings()

    return LLMConfig(
        provider=settings.llm_provider,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        api_key=settings.openai_api_key,
    )


def create_chat_model(
    config: LLMConfig | None = None,
) -> BaseChatModel:
    config = config or get_llm_config()

    if config.provider == "openai":
        return ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.api_key,
        )

    raise ValueError(
        f"Unsupported LLM provider: {config.provider}"
    )