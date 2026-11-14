import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from raas_ingestion.auth import TokenManager, TokenState
from raas_ingestion.client import WorkdayRaaSClient
from raas_ingestion.retry_policy import RetryConfig, RetryExhaustedError, RetryableHTTPError


class TestWorkdayRaaSIngestion(unittest.TestCase):
    def test_token_refreshes_within_buffer(self):
        now = [1000.0]
        calls = [0]

        def fetch():
            calls[0] += 1
            return TokenState(access_token=f"tok_{calls[0]}", expires_at=now[0] + 300)

        mgr = TokenManager(fetcher=fetch, buffer_seconds=60, clock=lambda: now[0])
        self.assertEqual(mgr.get_token(), "tok_1")
        now[0] = 1200.0
        self.assertEqual(mgr.get_token(), "tok_1")
        now[0] = 1245.0  # within 60s expiry buffer
        self.assertEqual(mgr.get_token(), "tok_2")
        self.assertEqual(calls[0], 2)

    def test_paginated_client_with_transient_429_retry(self):
        attempts = [0]
        mgr = TokenManager(lambda: TokenState("valid_tok", 9999999999.0), clock=lambda: 1000.0)

        def transport(url, headers, params):
            self.assertEqual(headers["Authorization"], "Bearer valid_tok")
            attempts[0] += 1
            if attempts[0] == 1:
                raise RetryableHTTPError(429, "Rate limited", retry_after=0.0)
            offset = params["offset"]
            if offset == 0:
                return {"Report_Entry": [{"id": 1}, {"id": 2}]}
            if offset == 2:
                return {"Report_Entry": [{"id": 3}]}
            return {"Report_Entry": []}

        client = WorkdayRaaSClient(
            token_manager=mgr,
            transport=transport,
            retry_config=RetryConfig(max_attempts=3, base_delay=0.0, jitter_ratio=0.0),
            page_size=2,
        )
        res = client.fetch_report("https://wd.example.com/raas/gl")
        self.assertEqual(res.total_records, 3)
        self.assertEqual(res.total_pages, 2)
        self.assertEqual([r["id"] for r in res.records], [1, 2, 3])

    def test_retry_exhaustion_raises(self):
        mgr = TokenManager(lambda: TokenState("tok", 9999999999.0), clock=lambda: 1000.0)

        def failing_transport(url, headers, params):
            raise RetryableHTTPError(503, "Service Unavailable", retry_after=0.0)

        client = WorkdayRaaSClient(
            token_manager=mgr,
            transport=failing_transport,
            retry_config=RetryConfig(max_attempts=2, base_delay=0.0, jitter_ratio=0.0),
        )
        with self.assertRaises(RetryExhaustedError):
            client.fetch_report("https://wd.example.com/raas/gl")


if __name__ == "__main__":
    unittest.main()
