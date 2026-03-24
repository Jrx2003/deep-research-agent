"""Search tools for Deep Research Agent."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
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
    relevance_score: float = 0.0  # Added for relevance checking


def calculate_relevance(query: str, title: str, content: str) -> float:
    """Calculate relevance score between query and result.

    Args:
        query: Search query
        title: Result title
        content: Result content/snippet

    Returns:
        Relevance score (0.0-1.0)
    """
    query_lower = query.lower()
    title_lower = title.lower()
    content_lower = content.lower()

    # Extract keywords from query (simple approach)
    keywords = [k for k in query_lower.split() if len(k) > 2]

    if not keywords:
        return 0.5

    # Check keyword presence in title and content
    title_matches = sum(1 for k in keywords if k in title_lower)
    content_matches = sum(1 for k in keywords if k in content_lower)

    # Title matches weighted more heavily
    title_score = title_matches / len(keywords) * 0.6
    content_score = min(content_matches / len(keywords), 1.0) * 0.4

    return title_score + content_score


def is_trusted_source(url: str) -> bool:
    """Check if URL is from a trusted source.

    Args:
        url: URL to check

    Returns:
        True if trusted
    """
    trusted_domains = [
        # Academic
        '.edu', 'arxiv.org', 'scholar.google',
        # Tech documentation
        'docs.', 'developer.', 'github.com',
        # Encyclopedia
        'wikipedia.org', 'wikidata.org',
        # News
        'techcrunch.com', 'wired.com', 'theverge.com',
        # Company blogs
        'anthropic.com', 'openai.com', 'google.com',
        # Chinese sources
        'zhihu.com', 'csdn.net', 'juejin.cn',
    ]

    domain = urlparse(url).netloc.lower()

    for trusted in trusted_domains:
        if trusted in domain:
            return True

    return False


def is_low_quality_source(url: str, title: str) -> bool:
    """Check if source is likely low quality.

    Args:
        url: URL
        title: Page title

    Returns:
        True if low quality
    """
    low_quality_indicators = [
        'baidu.com/question',  # Baidu Zhidao Q&A
        'zhidao.baidu',        # Baidu Q&A
        'tieba.baidu',         # Baidu Tieba forum
        'douyin.com',          # TikTok
        'kuaishou.com',        # Short video
    ]

    url_lower = url.lower()
    for indicator in low_quality_indicators:
        if indicator in url_lower:
            return True

    return False


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
            for r in ddgs.text(query, max_results=num_results * 2):  # Get more to filter
                title = r.get("title", "")
                url = r.get("href", "")
                content = r.get("body", "")

                # Skip low quality sources
                if is_low_quality_source(url, title):
                    continue

                # Calculate relevance
                relevance = calculate_relevance(query, title, content)

                # Boost score for trusted sources
                base_score = 0.8
                if is_trusted_source(url):
                    base_score = 0.95

                results.append(SearchResult(
                    title=title,
                    url=url,
                    content=content,
                    score=base_score,
                    source="duckduckgo",
                    relevance_score=relevance,
                ))

                if len(results) >= num_results:
                    break

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
            "num": num_results * 2,  # Get more to filter
        }

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        results = []
        for item in data.get("organic_results", []):
            title = item.get("title", "")
            url = item.get("link", "")
            content = item.get("snippet", "")

            # Skip low quality sources
            if is_low_quality_source(url, title):
                continue

            # Calculate relevance
            relevance = calculate_relevance(query, title, content)

            position = item.get("position", 1)
            score = 1.0 - (position - 1) * 0.1

            results.append(SearchResult(
                title=title,
                url=url,
                content=content,
                score=score,
                source="google",
                relevance_score=relevance,
            ))

            if len(results) >= num_results:
                break

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
            relevance_score=0.9,
        ),
        SearchResult(
            title=f"Latest Research on {query}",
            url=f"https://research.example.org/{query.replace(' ', '-')}",
            content=f"Recent research papers and studies about {query} have shown significant progress in the field, with new methodologies being developed.",
            score=0.88,
            source="mock",
            relevance_score=0.85,
        ),
        SearchResult(
            title=f"{query} - Wikipedia",
            url=f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            content=f"Wikipedia article covering the history, key concepts, and important figures related to {query}.",
            score=0.82,
            source="mock",
            relevance_score=0.88,
        ),
    ]

    return mock_results[:num_results]


def search(query: str, num_results: int = 5, min_relevance: float = 0.3) -> List[SearchResult]:
    """Search using available search providers.

    Args:
        query: Search query
        num_results: Number of results to return
        min_relevance: Minimum relevance score (0.0-1.0)

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
        if r.url not in seen_urls and r.relevance_score >= min_relevance:
            results.append(r)
            seen_urls.add(r.url)

    # If we have SerpAPI, supplement with Google results
    if settings.serpapi_api_key:
        serp_results = search_serpapi(query, num_results)
        for r in serp_results:
            if r.url not in seen_urls and r.relevance_score >= min_relevance:
                results.append(r)
                seen_urls.add(r.url)

    # Sort by combined score (base score + relevance)
    results.sort(key=lambda x: x.score + x.relevance_score, reverse=True)

    # If no results from real search, use mock
    if not results:
        print("No results from real search APIs, falling back to mock mode")
        return search_mock(query, num_results)

    # Check average relevance
    if results:
        avg_relevance = sum(r.relevance_score for r in results) / len(results)
        if avg_relevance < 0.4:
            print(f"Warning: Low average relevance ({avg_relevance:.2f}) for query: {query}")

    # Rate limiting
    time.sleep(0.5)

    return results[:num_results]


def search_multiple(queries: List[str], num_results: int = 5, min_relevance: float = 0.3) -> List[Dict[str, Any]]:
    """Search multiple queries and return combined results.

    Args:
        queries: List of search queries
        num_results: Number of results per query
        min_relevance: Minimum relevance score

    Returns:
        List of search results as dictionaries
    """
    all_results = []
    low_relevance_queries = []

    for query in queries:
        results = search(query, num_results, min_relevance)

        # Check if this query had low relevance results
        if results and all(r.source != "mock" for r in results):
            avg_relevance = sum(r.relevance_score for r in results) / len(results)
            if avg_relevance < 0.4:
                low_relevance_queries.append((query, avg_relevance))

        for r in results:
            all_results.append({
                "title": r.title,
                "url": r.url,
                "content": r.content,
                "score": r.score,
                "source": r.source,
                "relevance_score": r.relevance_score,
            })

    # Deduplicate by URL
    seen = set()
    unique_results = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique_results.append(r)

    # Warn about low relevance queries
    if low_relevance_queries:
        print("\nWarning: The following queries had low relevance results:")
        for query, score in low_relevance_queries:
            print(f"  - '{query}' (avg relevance: {score:.2f})")
        print("Consider refining these queries for better results.\n")

    return unique_results
