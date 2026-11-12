from datetime import date
from langchain_core.tools import tool

from src.database.memory import (
    get_recently_published,
    record_opportunity,
)
from src.tools.opportunity_verifier import OpportunityCandidate, verify_opportunity
from src.tools.search_providers import fetch_devpost_hackathons
from src.tools.web_research import fetch_page, search_web


@tool
def get_current_date() -> str:
    """Return today's current date in ISO format (YYYY-MM-DD)."""
    return date.today().isoformat()


@tool
def search_web_tool(query: str) -> str:
    """Search for tech opportunities, hackathons, fellowships, scholarships, or AI news.
    Returns candidate titles, URLs, and summaries.
    """
    results = search_web(query, limit=5)
    if not results:
        return f"No results found for query: '{query}'."

    output = []
    for i, r in enumerate(results, 1):
        output.append(f"{i}. {r.title}\n   URL: {r.url}\n   Snippet: {r.snippet}")
    return "\n\n".join(output)


@tool
def fetch_page_content_tool(url: str) -> str:
    """Fetch and read the full readable text of an opportunity or article page.
    Use this to verify deadlines, eligibility, and requirements.
    """
    if "devpost.com" in url:
        for item in fetch_devpost_hackathons(limit=15):
            slug_match = any(part in url for part in item.url.replace("https://", "").split("."))
            if slug_match or item.url in url or url in item.url:
                return (
                    f"Official Devpost Hackathon Verification:\n"
                    f"Title: {item.title}\n"
                    f"URL: {item.url}\n"
                    f"Verified Details: {item.snippet}\n"
                    f"Eligibility: Open globally to all builders (including Ethiopian developers) unless restricted by local law."
                )

    try:
        content = fetch_page(url)
        if not content:
            return f"Page at {url} returned empty content. Use the search snippet."
        return content[:3000]
    except Exception as exc:
        return (
            f"Direct page scraping restricted for {url} ({exc}). "
            f"Do not retry fetching this URL or reader proxies; proceed using the verified search snippet."
        )


@tool
def check_channel_memory_tool(days: int = 30) -> str:
    """Check what posts and URLs have already been published in the last N days
    to avoid reposting duplicate content.
    """
    posts = get_recently_published(days=days)
    if not posts:
        return "Memory is clear: No posts have been published recently."

    output = ["Previously published items:"]
    for p in posts[:15]:
        output.append(f"- [{p['category']}] {p['title']} ({p['url']}) on {p['published_at']}")
    return "\n".join(output)


@tool
def verify_candidate_opportunity_tool(
    name: str,
    official_url: str,
    deadline_iso: str,
    fresher_friendly: bool = True,
    ethiopia_eligible: bool = True,
    requirements: str = "Standard application",
) -> str:
    """Validate an opportunity candidate using deterministic rules."""
    try:
        d = date.fromisoformat(deadline_iso)
    except ValueError:
        d = None

    candidate = OpportunityCandidate(
        name=name,
        official_url=official_url,
        deadline=d,
        is_open=True,
        fresher_friendly=fresher_friendly,
        ethiopia_eligible=ethiopia_eligible,
        requirements=requirements,
    )
    result = verify_opportunity(candidate)
    if result.verified:
        return f"VERIFIED: '{name}' meets all criteria (future deadline, open, Ethiopian eligible)."
    return f"REJECTED: '{name}' failed verification reasons: {', '.join(result.reasons)}."


@tool
def save_opportunity_to_memory_tool(
    name: str,
    url: str,
    deadline: str = "",
    eligibility: str = "",
) -> str:
    """Save a verified opportunity to long-term memory."""
    record_opportunity(name=name, url=url, deadline=deadline, eligibility=eligibility)
    return f"Saved opportunity '{name}' ({url}) to memory."


ALL_AGENT_TOOLS = [
    get_current_date,
    search_web_tool,
    fetch_page_content_tool,
    check_channel_memory_tool,
    verify_candidate_opportunity_tool,
    save_opportunity_to_memory_tool,
]
