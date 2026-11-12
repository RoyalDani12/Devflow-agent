import base64
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import json
import os
import re
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT_SECONDS = 8
MAX_PAGE_CHARS = 3_500
MAX_EVIDENCE_CHARS = 12_000


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


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
                self.results.append(
                    SearchResult(self._title.strip(), url, self._snippet.strip())
                )
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


def _unwrap_bing_url(url: str) -> str:
    decoded_url = unescape(url)
    match = re.search(r"[?&]u=a1([a-zA-Z0-9_\-]+)", decoded_url)
    if match:
        token = match.group(1)
        padded = token + "=" * (-len(token) % 4)
        try:
            return base64.urlsafe_b64decode(padded).decode("utf-8", errors="ignore")
        except Exception:
            pass
    return decoded_url


def _fetch_devpost_hackathons(limit: int = 5) -> list[SearchResult]:
    """Fetch live hackathons from the official Devpost API."""
    url = (
        "https://devpost.com/api/hackathons?"
        "challenge_type[]=online&status[]=upcoming&status[]=open"
    )
    results = []
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        for h in data.get("hackathons", [])[:limit]:
            title = f"{h.get('title')} ({h.get('submission_period_dates')})"
            url_link = h.get("url") or ""
            prize = re.sub(r"<[^>]+>", "", str(h.get("prize_amount", ""))).strip()
            themes = ", ".join(t.get("name", "") for t in h.get("themes", []))
            snippet = (
                f"Devpost Online Hackathon. Prize: {prize}. Themes: {themes}. "
                f"Status: {h.get('open_state')}. Time left: {h.get('time_left_to_submission')}."
            )
            if title and url_link:
                results.append(SearchResult(title, url_link, snippet))
    except (OSError, ValueError):
        pass
    return results


def _fetch_ethiopia_scholarships(limit: int = 5) -> list[SearchResult]:
    """Fetch active scholarships and fellowships open to Ethiopians from scholarship.et."""
    results = []
    seen = set()
    try:
        req = Request("https://scholarship.et/scholarships", headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        links = re.findall(
            r'href=[\"\'](/scholarships/([^\"\']+))[\"\'][^>]*>(.*?)</a>',
            html,
            re.DOTALL,
        )
        for path, slug, text in links:
            full_url = f"https://scholarship.et{path}"
            clean_title = re.sub(r"<[^>]+>", "", text).strip()
            slug_title = slug.rsplit("-", 1)[0].replace("-", " ").title()
            title = clean_title if clean_title and len(clean_title) > 6 else slug_title
            if full_url not in seen and len(title) > 6:
                seen.add(full_url)
                snippet = (
                    f"Scholarship / fellowship opportunity open to Ethiopian applicants: {title}. "
                    "Verified on scholarship.et."
                )
                results.append(SearchResult(title, full_url, snippet))
                if len(results) >= limit:
                    break
    except (OSError, ValueError):
        pass
    return results


def _fetch_opportunitydesk(limit: int = 5) -> list[SearchResult]:
    """Fetch fresh international fellowships and scholarships from Opportunity Desk."""
    results = []
    try:
        req = Request("https://opportunitydesk.org/feed/", headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            root = ElementTree.fromstring(resp.read())
        for it in root.findall(".//item")[:limit]:
            title = it.findtext("title", default="").strip()
            url_link = it.findtext("link", default="").strip()
            raw_desc = it.findtext("description", default="")
            snippet = re.sub(r"<[^>]+>", "", raw_desc).strip()
            if title and url_link:
                results.append(SearchResult(title, url_link, snippet))
    except (OSError, ValueError, ElementTree.ParseError):
        pass
    return results


def _fetch_techcrunch_ai(limit: int = 5) -> list[SearchResult]:
    """Fetch latest AI product releases and research from TechCrunch AI feed."""
    results = []
    try:
        req = Request(
            "https://techcrunch.com/category/artificial-intelligence/feed/",
            headers={"User-Agent": USER_AGENT},
        )
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            root = ElementTree.fromstring(resp.read())
        for it in root.findall(".//item")[:limit]:
            title = it.findtext("title", default="").strip()
            url_link = it.findtext("link", default="").strip()
            raw_desc = it.findtext("description", default="")
            snippet = re.sub(r"<[^>]+>", "", raw_desc).strip()
            if title and url_link:
                results.append(SearchResult(title, url_link, snippet))
    except (OSError, ValueError, ElementTree.ParseError):
        pass
    return results


def _search_tavily(query: str, api_key: str, limit: int = 5) -> list[SearchResult]:
    """Search using Tavily API if configured."""
    results = []
    try:
        payload = json.dumps({"query": query, "max_results": limit}).encode("utf-8")
        req = Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        for item in data.get("results", []):
            title = item.get("title", "")
            url_link = item.get("url", "")
            snippet = item.get("content", "")
            if title and url_link:
                results.append(SearchResult(title, url_link, snippet))
    except (OSError, ValueError):
        pass
    return results


def search_web(query: str, limit: int = 5) -> list[SearchResult]:
    """Search web indexes, specialized APIs, and feeds for current information."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        api_results = _search_tavily(query, tavily_key, limit)
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
    is_opp = any(
        k in lower_query
        for k in [
            "opportunity",
            "oppent",
            "fellowship",
            "follewship",
            "scholarship",
            "schollar",
            "internship",
            "grant",
            "ethiopia",
        ]
    )
    is_news = any(k in lower_query for k in ["ai", "news", "model", "release", "tech"])

    if is_hackathon:
        add_results(_fetch_devpost_hackathons(limit))

    if is_opp:
        add_results(_fetch_ethiopia_scholarships(limit))
        add_results(_fetch_opportunitydesk(limit))

    if is_news and not is_opp:
        add_results(_fetch_techcrunch_ai(limit))

    if len(combined_results) >= limit:
        return combined_results[:limit]

    # Try DuckDuckGo
    params = urlencode({"q": query, "kl": "us-en"})
    for endpoint in (
        f"https://lite.duckduckgo.com/lite/?{params}",
        f"https://html.duckduckgo.com/html/?{params}",
    ):
        try:
            request = Request(endpoint, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
                parser = _SearchResultParser()
                parser.feed(response.read().decode("utf-8", errors="replace"))
            if parser.results:
                add_results(parser.results)
                break
        except OSError:
            continue

    # Try Google News RSS
    if len(combined_results) < limit:
        try:
            rss_request = Request(
                "https://news.google.com/rss/search?"
                + urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}),
                headers={"User-Agent": USER_AGENT},
            )
            with urlopen(rss_request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
                root = ElementTree.fromstring(response.read())
            rss_items = []
            for item in root.findall(".//item"):
                title = item.findtext("title", default="").strip()
                url_link = item.findtext("link", default="").strip()
                snippet = item.findtext("description", default="").strip()
                if title and url_link:
                    rss_items.append(SearchResult(title, url_link, snippet))
            add_results(rss_items)
        except (OSError, ElementTree.ParseError):
            pass

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

    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        html = response.read().decode("utf-8", errors="replace")

    parser = _TextParser()
    parser.feed(html)
    return " ".join(parser.text)[:MAX_PAGE_CHARS]


def collect_page_evidence(
    queries: list[str],
    result_limit: int = 4,
    page_limit: int = 6,
) -> str:
    """Search queries and fetch candidate pages as labelled evidence."""
    results: list[SearchResult] = []
    seen_urls: set[str] = set()
    for query in queries:
        for result in search_web(query, result_limit):
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                results.append(result)

    evidence: list[str] = []
    for result in results[:page_limit]:
        page_text = ""
        try:
            page_text = fetch_page(result.url)
        except (OSError, ValueError):
            page_text = result.snippet

        if not page_text and result.snippet:
            page_text = result.snippet

        if not page_text:
            continue

        evidence.append(
            f"SOURCE URL: {result.url}\n"
            f"SEARCH TITLE: {result.title}\n"
            f"PAGE CONTENT: {page_text}"
        )
    return "\n\n--- CANDIDATE SOURCE ---\n\n".join(evidence)[:MAX_EVIDENCE_CHARS]
