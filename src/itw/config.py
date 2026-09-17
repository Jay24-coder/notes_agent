import os
from dataclasses import dataclass

from dotenv import load_dotenv
from loguru import logger

from itw.errors import ItwError

load_dotenv()

EMBEDDING_DIMENSION = 1536


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_embedding_model: str
    openai_chat_model: str
    typesense_host: str
    typesense_port: int
    typesense_protocol: str
    typesense_api_key: str
    typesense_collection: str
    retrieval_max_vector_distance: float
    tavily_api_key: str


def settings_debug_summary(settings: Settings) -> str:
    """Non-secret settings summary safe for DEBUG logs."""
    return (
        f"host={settings.typesense_host}:{settings.typesense_port} "
        f"protocol={settings.typesense_protocol} "
        f"collection={settings.typesense_collection} "
        f"embedding_model={settings.openai_embedding_model} "
        f"chat_model={settings.openai_chat_model} "
        f"max_vector_distance={settings.retrieval_max_vector_distance} "
        f"openai_key={'set' if settings.openai_api_key else 'unset'} "
        f"typesense_key={'set' if settings.typesense_api_key else 'unset'} "
        f"tavily_key={'set' if settings.tavily_api_key else 'unset'}"
    )


def load_settings() -> Settings:
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        raise ItwError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    typesense_api_key = os.getenv("TYPESENSE_API_KEY", "").strip()
    if not typesense_api_key:
        raise ItwError(
            "TYPESENSE_API_KEY is not set. Use the key from docker-compose (default: xyz)."
        )

    try:
        port = int(os.getenv("TYPESENSE_PORT", "8108"))
    except ValueError:
        raise ItwError("TYPESENSE_PORT must be an integer.") from None

    try:
        max_dist = float(os.getenv("RETRIEVAL_MAX_VECTOR_DISTANCE", "0.45"))
    except ValueError:
        raise ItwError("RETRIEVAL_MAX_VECTOR_DISTANCE must be a number.") from None

    settings = Settings(
        openai_api_key=openai_api_key,
        openai_embedding_model=os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        ),
        openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        typesense_host=os.getenv("TYPESENSE_HOST", "localhost"),
        typesense_port=port,
        typesense_protocol=os.getenv("TYPESENSE_PROTOCOL", "http"),
        typesense_api_key=typesense_api_key,
        typesense_collection=os.getenv("TYPESENSE_COLLECTION", "notes"),
        retrieval_max_vector_distance=max_dist,
        tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip(),
    )
    logger.debug("Loaded settings: {}", settings_debug_summary(settings))
    return settings
