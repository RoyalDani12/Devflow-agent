from dataclasses import dataclass
import json
import os
import re
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from src.database.memory import get_seen_opportunity_urls

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT_SECONDS = 8


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


def fetch_devpost_hackathons(limit: int = 6) -> list[SearchResult]:
    """Fetch live hackathons from official Devpost API, prioritizing unseen items."""
    seen_urls = get_seen_opportunity_urls()
    url = "https://devpost.com/api/hackathons?challenge_type[]=online&status[]=upcoming&status[]=open"
    results = []
    unseen_results = []
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        for h in data.get("hackathons", []):
            title = f"{h.get('title')} ({h.get('submission_period_dates')})"
            url_link = h.get("url") or ""
            prize = re.sub(r"<[^>]+>", "", str(h.get("prize_amount", ""))).strip()
            themes = ", ".join(t.get("name", "") for t in h.get("themes", []))
            snippet = (
                f"Devpost Online Hackathon. Prize: {prize}. Themes: {themes}. "
                f"Status: {h.get('open_state')}. Time left: {h.get('time_left_to_submission')}."
            )
            if title and url_link:
                item = SearchResult(title, url_link, snippet)
                if url_link in seen_urls:
                    results.append(item)
                else:
                    unseen_results.append(item)
    except (OSError, ValueError):
        pass
    return (unseen_results + results)[:limit]


def fetch_ethiopia_scholarships(limit: int = 8) -> list[SearchResult]:
    """Fetch active scholarships and fellowships open to Ethiopians, rotating unseen items."""
    seen_urls = get_seen_opportunity_urls()
    results = []
    unseen_results = []
    seen_in_batch = set()

    sources = [
        ("https://scholarship.et/scholarships", r'href=[\"\'](/scholarships/([^\"\']+))[\"\'][^>]*>(.*?)</a>', "https://scholarship.et"),
        ("https://www.ethioopportunity.com/", r'href=[\"\'](/detail/([^\"\']+))[\"\'][^>]*>(.*?)</a>', "https://www.ethioopportunity.com"),
    ]

    for source_url, pattern, base_url in sources:
        try:
            req = Request(source_url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            links = re.findall(pattern, html, re.DOTALL)
            for path, slug, text in links:
                full_url = f"{base_url}{path}"
                clean_title = re.sub(r"<[^>]+>", "", text).strip()
                slug_title = slug.replace("_", " ").rsplit("-", 1)[0].replace("-", " ").title()
                title = clean_title if clean_title and len(clean_title) > 6 else slug_title
                if full_url not in seen_in_batch and len(title) > 6:
                    seen_in_batch.add(full_url)
                    snippet = f"Verified fellowship / scholarship for Ethiopian applicants: {title}."
                    item = SearchResult(title, full_url, snippet)
                    if full_url in seen_urls:
                        results.append(item)
                    else:
                        unseen_results.append(item)
        except (OSError, ValueError):
            continue

    return (unseen_results + results)[:limit]


def fetch_opportunity_feeds(limit: int = 8) -> list[SearchResult]:
    """Fetch opportunities from OpportunitiesForAfricans, Scholars4Dev, and OpportunityDesk."""
    seen_urls = get_seen_opportunity_urls()
    results = []
    unseen_results = []
    feeds = [
        ("https://www.opportunitiesforafricans.com/feed/", "Opportunities for Africans"),
        ("https://www.scholars4dev.com/feed/", "Scholars4Dev"),
        ("https://opportunitydesk.org/feed/", "Opportunity Desk"),
    ]
    for feed_url, label in feeds:
        try:
            req = Request(feed_url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
                root = ElementTree.fromstring(resp.read())
            for it in root.findall(".//item"):
                title = it.findtext("title", default="").strip()
                url_link = it.findtext("link", default="").strip()
                raw_desc = it.findtext("description", default="")
                snippet = re.sub(r"<[^>]+>", "", raw_desc).strip()
                if title and url_link:
                    item = SearchResult(title, url_link, f"[{label}] {snippet[:180]}")
                    if url_link in seen_urls:
                        results.append(item)
                    else:
                        unseen_results.append(item)
        except (OSError, ValueError, ElementTree.ParseError):
            continue
    return (unseen_results + results)[:limit]


fetch_opportunitydesk = fetch_opportunity_feeds


def fetch_techcrunch_ai(limit: int = 5) -> list[SearchResult]:
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


def search_tavily(query: str, api_key: str, limit: int = 5) -> list[SearchResult]:
    """Search using Tavily API if configured."""
    results = []
    try:
        payload = json.dumps({"query": query, "max_results": limit}).encode("utf-8")
        req = Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
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
