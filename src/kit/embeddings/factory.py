from langchain_openai import OpenAIEmbeddings

from kit.config import get_settings


def create_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()

    if settings.embedding_provider != "openai":
        raise ValueError(
            f"Unsupported embedding provider: {settings.embedding_provider}"
        )

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
