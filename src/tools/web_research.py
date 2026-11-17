from html import unescape
from html.parser import HTMLParser
import os
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from src.database.memory import get_seen_opportunity_urls
from src.tools.media_service import extract_og_image_from_html, register_url_image
from src.tools.search_providers import (
    DEFAULT_TIMEOUT_SECONDS,
    SearchResult,
    USER_AGENT,
    fetch_devpost_hackathons,
    fetch_ethiopia_scholarships,
    fetch_opportunitydesk,
    fetch_techcrunch_ai,
    search_tavily,
)

MAX_PAGE_CHARS = 1_500
MAX_EVIDENCE_CHARS = 5_000


class _SearchResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[SearchResult] = []
        self._title = ""
        self._href = ""
        self._snippet = ""
        self._in_title = False
        self._in_snippet = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = attributes.get("class", "") or ""
        if tag == "a" and {"result__a", "result-link"} & set(classes.split()):
            self._href = attributes.get("href", "") or ""
            self._title = ""
            self._in_title = True
        elif {"result__snippet", "result-snippet"} & set(classes.split()):
            self._snippet = ""
            self._in_snippet = True

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title += unescape(data)
        if self._in_snippet:
            self._snippet += unescape(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_title:
            url = _unwrap_search_url(self._href)
            if self._title and url:
                self.results.append(SearchResult(self._title.strip(), url, self._snippet.strip()))
            self._in_title = False
        if self._in_snippet:
            self._in_snippet = False


def _unwrap_search_url(url: str) -> str:
    if url.startswith("//"):
        url = f"https:{url}"
    parsed = urlparse(url)
    if parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(target)
    return url if parsed.scheme in {"http", "https"} else ""


def search_web(query: str, limit: int = 5) -> list[SearchResult]:
    """Search web indexes, specialized APIs, and feeds for current information."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        api_results = search_tavily(query, tavily_key, limit)
        if api_results:
            return api_results[:limit]

    lower_query = query.lower()
    combined_results: list[SearchResult] = []
    seen_urls: set[str] = set()

    def add_results(items: list[SearchResult]):
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                combined_results.append(item)

    is_hackathon = any(k in lower_query for k in ["hackathon", "hackatoon", "hack", "contest"])
    is_opp = any(k in lower_query for k in ["opp", "fellow", "foll", "scholar", "intern", "grant", "ethiop"])
    is_news = any(k in lower_query for k in ["ai", "news", "model", "release", "tech"])

    if is_hackathon:
        add_results(fetch_devpost_hackathons(limit))
    if is_opp:
        add_results(fetch_ethiopia_scholarships(limit))
        add_results(fetch_opportunitydesk(limit))
    if is_news and not is_opp:
        add_results(fetch_techcrunch_ai(limit))

    if len(combined_results) >= limit:
        return combined_results[:limit]

    # DuckDuckGo fallback
    params = urlencode({"q": query, "kl": "us-en"})
    for endpoint in (f"https://lite.duckduckgo.com/lite/?{params}", f"https://html.duckduckgo.com/html/?{params}"):
        try:
            req = Request(endpoint, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
                parser = _SearchResultParser()
                parser.feed(resp.read().decode("utf-8", errors="replace"))
            if parser.results:
                add_results(parser.results)
                break
        except OSError:
            continue

    return combined_results[:limit]


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg", "nav", "footer"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "nav", "footer"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            cleaned = data.strip()
            if cleaned:
                self.text.append(cleaned)


def fetch_page(url: str) -> str:
    """Fetch readable text from one candidate page for model verification."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Unsupported page URL: {url}")

    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    og_img = extract_og_image_from_html(html)
    if og_img:
        register_url_image(url, og_img)

    parser = _TextParser()
    parser.feed(html)
    return " ".join(parser.text)[:MAX_PAGE_CHARS]


def collect_page_evidence(queries: list[str], result_limit: int = 4, page_limit: int = 6) -> str:
    """Search queries and fetch candidate pages as labelled evidence."""
    results: list[SearchResult] = []
    seen_urls: set[str] = set()
    for query in queries:
        for result in search_web(query, result_limit):
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                results.append(result)

    db_seen = get_seen_opportunity_urls()
    unseen_items = [r for r in results if r.url not in db_seen]
    seen_items = [r for r in results if r.url in db_seen]
    ordered_results = (unseen_items + seen_items)[:page_limit]

    evidence: list[str] = []
    for result in ordered_results:
        page_text = ""
        try:
            page_text = fetch_page(result.url)
        except (OSError, ValueError):
            page_text = result.snippet

        if not page_text and result.snippet:
            page_text = result.snippet
        if not page_text:
            continue

        if getattr(result, "image_url", None):
            register_url_image(result.url, result.image_url)
            img_line = f"\nIMAGE URL: {result.image_url}"
        else:
            img_line = ""
        evidence.append(f"SOURCE URL: {result.url}{img_line}\nSEARCH TITLE: {result.title}\nPAGE CONTENT: {page_text}")
    return "\n\n--- CANDIDATE SOURCE ---\n\n".join(evidence)[:MAX_EVIDENCE_CHARS]
