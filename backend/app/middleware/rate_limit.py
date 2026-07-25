"""Lightweight in-memory rate limiting for expensive public endpoints.

The AI/LLM-backed endpoints (RAG, research recommendations, macro interpretation,
insights) are intentionally reachable without authentication so the public
product demo works. That also makes them a cost/DoS surface: each call invokes a
paid LLM. This module caps per-client request rate with a sliding window.

Storage is in-process (per Cloud Run instance). That is deliberately simple —
it is an abuse-mitigation guardrail, not a distributed quota. With multiple
instances the effective limit scales with instance count, which is acceptable
for stopping runaway loops and scrapers.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

# Keep the per-IP table from growing without bound on a long-lived instance.
_MAX_TRACKED_KEYS = 10_000


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        dq = self._hits[key]
        while dq and dq[0] < cutoff:
            dq.popleft()

        if len(dq) >= self.max_requests:
            retry_after = max(1, int(dq[0] + self.window_seconds - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down and try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )
        dq.append(now)

        # Opportunistic cleanup: if the table is large, drop keys whose windows
        # have fully expired so idle clients don't accumulate forever.
        if len(self._hits) > _MAX_TRACKED_KEYS:
            for k in [k for k, d in self._hits.items() if not d or d[-1] < cutoff]:
                del self._hits[k]


def _client_key(request: Request) -> str:
    # Cloud Run terminates TLS and sets X-Forwarded-For: <client>, <proxies...>.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(max_requests: int, window_seconds: int):
    """Build a FastAPI dependency enforcing a per-client sliding-window limit."""
    limiter = SlidingWindowLimiter(max_requests, window_seconds)

    def dependency(request: Request) -> None:
        limiter.check(_client_key(request))

    return dependency


# Shared budget across all AI/LLM endpoints: 20 calls per minute per client.
ai_rate_limit = rate_limit(max_requests=20, window_seconds=60)
