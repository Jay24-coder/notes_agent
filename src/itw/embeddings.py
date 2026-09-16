from openai import OpenAI

from itw.config import Settings
from itw.errors import ItwError


def embed_text(settings: Settings, text: str) -> list[float]:
    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
    except Exception as exc:  # noqa: BLE001 — surface provider errors to CLI
        raise ItwError(f"OpenAI embedding request failed: {exc}") from exc

    if not response.data:
        raise ItwError("OpenAI returned no embedding data.")

    return response.data[0].embedding
