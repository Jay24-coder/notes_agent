from __future__ import annotations

import json
import urllib.parse
import urllib.request

from itw.errors import ItwError


def live_web_search(query: str) -> str:
    """Lightweight DuckDuckGo instant-answer lookup (no API key)."""
    url = (
        "https://api.duckduckgo.com/?"
        + urllib.parse.urlencode({"q": query, "format": "json", "no_redirect": 1})
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ItwError(f"Live web search failed: {exc}") from exc

    abstract = (payload.get("AbstractText") or "").strip()
    heading = (payload.get("Heading") or "").strip()
    if abstract:
        source = heading or payload.get("AbstractSource") or "DuckDuckGo"
        return f"{abstract}\n(Source hint: {source})"

    related = payload.get("RelatedTopics") or []
    snippets: list[str] = []
    for item in related[:3]:
        if isinstance(item, dict) and item.get("Text"):
            snippets.append(str(item["Text"]))
    if snippets:
        return "\n".join(snippets)

    raise ItwError("Live web search returned no usable results for this query.")
