"""Web scraping tools for Deep Research Agent."""

from typing import Optional
import re

try:
    import requests
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


def fetch_url(url: str, timeout: int = 10) -> Optional[str]:
    """Fetch content from a URL.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content or None if failed
    """
    if not BS4_AVAILABLE:
        return None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def extract_content(html: str, max_length: int = 5000) -> str:
    """Extract main content from HTML.

    Args:
        html: HTML content
        max_length: Maximum length of extracted content

    Returns:
        Extracted text content
    """
    if not BS4_AVAILABLE or not html:
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Try to find main content
        main_content = None

        # Common content containers
        for selector in ["main", "article", "[role='main']", ".content", "#content", ".post"]:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # Fallback to body if no main content found
        if not main_content:
            main_content = soup.find("body")

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        text = re.sub(r"\n+", "\n", text)
        text = re.sub(r" +", " ", text)

        return text[:max_length]

    except Exception as e:
        print(f"Failed to extract content: {e}")
        return ""


def fetch_and_extract(url: str, max_length: int = 5000) -> str:
    """Fetch URL and extract content.

    Args:
        url: URL to fetch
        max_length: Maximum length of extracted content

    Returns:
        Extracted text content
    """
    html = fetch_url(url)
    if html:
        return extract_content(html, max_length)
    return ""
