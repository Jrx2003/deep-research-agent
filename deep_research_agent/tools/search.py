"""Search tools for Deep Research Agent."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time
import os

from deep_research_agent.core.config import settings


@dataclass
class SearchResult:
    """Search result item."""

    title: str
    url: str
    content: str
    score: float = 0.0
    source: str = "duckduckgo"


def search_duckduckgo(query: str, num_results: int = 5) -> List[SearchResult]:
    """Search using DuckDuckGo.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of search results
    """
    results = []
    try:
        # Try new ddgs package first
        try:
            from ddgs import DDGS
        except ImportError:
            # Fall back to old package name
            from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num_results):
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    content=r.get("body", ""),
                    score=0.8,
                    source="duckduckgo",
                ))
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")

    return results


def search_serpapi(query: str, num_results: int = 5) -> List[SearchResult]:
    """Search using SerpAPI (Google).

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of search results
    """
    if not settings.serpapi_api_key:
        return []

    try:
        import requests

        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": settings.serpapi_api_key,
            "engine": "google",
            "num": num_results,
        }

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        results = []
        for item in data.get("organic_results", [])[:num_results]:
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                content=item.get("snippet", ""),
                score=item.get("position", 0) / num_results,
                source="google",
            ))

        return results

    except Exception as e:
        print(f"SerpAPI search failed: {e}")
        return []


def search_mock(query: str, num_results: int = 5) -> List[SearchResult]:
    """Mock search for testing without real search API.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        Mock search results
    """
    print(f"[MOCK SEARCH] Query: {query}")

    # Generate mock results based on query
    mock_results = [
        SearchResult(
            title=f"Understanding {query}",
            url=f"https://example.com/{query.replace(' ', '-').lower()}",
            content=f"This is a comprehensive guide about {query}. It covers the fundamental concepts, recent developments, and future implications in this field.",
            score=0.95,
            source="mock",
        ),
        SearchResult(
            title=f"Latest Research on {query}",
            url=f"https://research.example.org/{query.replace(' ', '-')}",
            content=f"Recent research papers and studies about {query} have shown significant progress in the field, with new methodologies being developed.",
            score=0.88,
            source="mock",
        ),
        SearchResult(
            title=f"{query} - Wikipedia",
            url=f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            content=f"Wikipedia article covering the history, key concepts, and important figures related to {query}.",
            score=0.82,
            source="mock",
        ),
    ]

    return mock_results[:num_results]


def search(query: str, num_results: int = 5) -> List[SearchResult]:
    """Search using available search providers.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of search results
    """
    # Check if mock mode is enabled (for testing)
    if os.getenv("SEARCH_MOCK_MODE", "false").lower() == "true":
        return search_mock(query, num_results)

    results = []
    seen_urls = set()

    # Try DuckDuckGo first (free, no API key)
    ddgs_results = search_duckduckgo(query, num_results)
    for r in ddgs_results:
        if r.url not in seen_urls:
            results.append(r)
            seen_urls.add(r.url)

    # If we have SerpAPI, supplement with Google results
    if settings.serpapi_api_key:
        serp_results = search_serpapi(query, num_results)
        for r in serp_results:
            if r.url not in seen_urls:
                results.append(r)
                seen_urls.add(r.url)

    # If no results from real search, use mock
    if not results:
        print("No results from real search APIs, falling back to mock mode")
        return search_mock(query, num_results)

    # Rate limiting
    time.sleep(0.5)

    return results[:num_results]


def search_multiple(queries: List[str], num_results: int = 5) -> List[Dict[str, Any]]:
    """Search multiple queries and return combined results.

    Args:
        queries: List of search queries
        num_results: Number of results per query

    Returns:
        List of search results as dictionaries
    """
    all_results = []

    for query in queries:
        results = search(query, num_results)
        for r in results:
            all_results.append({
                "title": r.title,
                "url": r.url,
                "content": r.content,
                "score": r.score,
                "source": r.source,
            })

    # Deduplicate by URL
    seen = set()
    unique_results = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique_results.append(r)

    return unique_results
