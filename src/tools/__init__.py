"""Tools for Deep Research Agent."""

from .search import search, search_multiple, SearchResult
from .scraper import fetch_url, extract_content
from .storage import save_report, load_state, save_state

__all__ = [
    "search",
    "search_multiple",
    "SearchResult",
    "fetch_url",
    "extract_content",
    "save_report",
    "load_state",
    "save_state",
]
