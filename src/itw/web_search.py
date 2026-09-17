from __future__ import annotations

from dataclasses import dataclass

from tavily import TavilyClient

from itw.errors import ItwError


@dataclass(frozen=True)
class LiveWebSearchResult:
    body: str
    source_urls: list[str]


def _require_tavily_key(tavily_api_key: str) -> str:
    key = tavily_api_key.strip()
    if not key:
        raise ItwError(
            "TAVILY_API_KEY is not set. Add it to .env when using --web-search."
        )
    return key


def live_web_search(query: str, *, tavily_api_key: str) -> LiveWebSearchResult:
    """Tavily Search for out-of-coverage questions (--web-search only)."""
    api_key = _require_tavily_key(tavily_api_key)
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
            topic="general",
        )
    except Exception as exc:  # noqa: BLE001
        raise ItwError(f"Live web search failed: {exc}") from exc

    results = response.get("results") or []
    source_urls: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        url = (item.get("url") or "").strip()
        if url and url not in source_urls:
            source_urls.append(url)

    answer = (response.get("answer") or "").strip()
    if answer:
        body = answer
    else:
        snippets: list[str] = []
        for item in results[:5]:
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or "").strip()
            content = (item.get("content") or "").strip()
            url = (item.get("url") or "").strip()
            if not content and not title:
                continue
            line = title or url or "Result"
            if content:
                line = f"{line}: {content}"
            if url:
                line = f"{line} ({url})"
            snippets.append(line)
        if not snippets:
            raise ItwError("Live web search returned no usable results for this query.")
        body = "\n\n".join(snippets)

    if source_urls:
        body += "\n\nLive search sources:\n" + "\n".join(f"- {u}" for u in source_urls)

    return LiveWebSearchResult(body=body, source_urls=source_urls)
