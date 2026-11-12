from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse


@dataclass(frozen=True)
class OpportunityCandidate:
    name: str
    official_url: str
    deadline: date | None
    is_open: bool
    fresher_friendly: bool
    ethiopia_eligible: bool
    requirements: str


@dataclass(frozen=True)
class VerificationResult:
    candidate: OpportunityCandidate
    verified: bool
    reasons: tuple[str, ...] = ()


def verify_opportunity(
    candidate: OpportunityCandidate,
    today: date | None = None,
) -> VerificationResult:
    """Reject a candidate unless its critical facts pass deterministic checks."""
    check_date = today or date.today()
    reasons: list[str] = []
    parsed_url = urlparse(candidate.official_url)

    if parsed_url.scheme != "https" or not parsed_url.netloc:
        reasons.append("official_url must be an HTTPS URL")
    if not candidate.name.strip():
        reasons.append("name is missing")
    if candidate.deadline is None:
        reasons.append("deadline is missing or unclear")
    elif candidate.deadline <= check_date:
        reasons.append("deadline is not in the future")
    if not candidate.is_open:
        reasons.append("applications are not confirmed open")
    if not candidate.fresher_friendly:
        reasons.append("not suitable for freshers")
    if not candidate.ethiopia_eligible:
        reasons.append("Ethiopian applicants are not confirmed eligible")
    if not candidate.requirements.strip():
        reasons.append("application requirements are missing")

    return VerificationResult(candidate, not reasons, tuple(reasons))


def verified_opportunities(
    candidates: list[OpportunityCandidate],
    today: date | None = None,
    limit: int = 3,
) -> list[OpportunityCandidate]:
    """Return verified candidates, preferring one open to Ethiopian applicants."""
    verified = [
        candidate
        for candidate in candidates
        if verify_opportunity(candidate, today).verified
    ]
    ethiopian = [candidate for candidate in verified if candidate.ethiopia_eligible]
    remaining = [candidate for candidate in verified if candidate not in ethiopian]
    return (ethiopian + remaining)[:limit]
