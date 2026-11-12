import unittest
from datetime import date, timedelta

from src.tools.opportunity_verifier import (
    OpportunityCandidate,
    verify_opportunity,
    verified_opportunities,
)


def candidate(**overrides):
    values = {
        "name": "Open opportunity",
        "official_url": "https://official.example/apply",
        "deadline": date(2099, 12, 31),
        "is_open": True,
        "fresher_friendly": True,
        "ethiopia_eligible": True,
        "requirements": "Complete the official application form.",
    }
    values.update(overrides)
    return OpportunityCandidate(**values)


class OpportunityVerifierTests(unittest.TestCase):
    def test_accepts_future_open_fresher_opportunity(self):
        result = verify_opportunity(candidate(), today=date(2026, 11, 12))

        self.assertTrue(result.verified)
        self.assertEqual(result.reasons, ())

    def test_rejects_expired_or_unclear_opportunity(self):
        result = verify_opportunity(
            candidate(deadline=date(2026, 11, 11)),
            today=date(2026, 11, 12),
        )
        unclear = verify_opportunity(candidate(deadline=None))

        self.assertFalse(result.verified)
        self.assertIn("deadline is not in the future", result.reasons)
        self.assertFalse(unclear.verified)

    def test_rejects_missing_eligibility_and_non_official_url(self):
        result = verify_opportunity(
            candidate(
                official_url="http://search.example/result",
                fresher_friendly=False,
                ethiopia_eligible=False,
            )
        )

        self.assertFalse(result.verified)
        self.assertEqual(len(result.reasons), 3)

    def test_limits_results_and_prioritizes_ethiopian_eligibility(self):
        candidates = [
            candidate(name="Other", ethiopia_eligible=True),
            candidate(name="Ethiopian", ethiopia_eligible=True),
            candidate(name="Another", ethiopia_eligible=True),
            candidate(name="Extra", deadline=date.today() - timedelta(days=1)),
        ]

        results = verified_opportunities(candidates, today=date(2026, 11, 12))

        self.assertEqual(
            [item.name for item in results],
            ["Other", "Ethiopian", "Another"],
        )


if __name__ == "__main__":
    unittest.main()
