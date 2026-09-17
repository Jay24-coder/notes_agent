from openai import OpenAI
from loguru import logger

from itw.config import Settings
from itw.errors import ItwError


def embed_text(settings: Settings, text: str) -> list[float]:
    client = OpenAI(api_key=settings.openai_api_key)
    logger.debug(
        "Embedding request model={} input_chars={}",
        settings.openai_embedding_model,
        len(text),
    )
    try:
        response = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
    except Exception as exc:  # noqa: BLE001 — surface provider errors to CLI
        logger.exception("OpenAI embedding request failed")
        raise ItwError(f"OpenAI embedding request failed: {exc}") from exc

    if not response.data:
        raise ItwError("OpenAI returned no embedding data.")

    embedding = response.data[0].embedding
    logger.debug("Embedding complete dims={}", len(embedding))
    return embedding
