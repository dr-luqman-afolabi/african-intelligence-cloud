import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_request_count: dict[str, int] = defaultdict(int)
_error_count: dict[str, int] = defaultdict(int)
_latency_sum: dict[str, float] = defaultdict(float)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Track per-route request count, error rate, and cumulative latency in-process."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        key = f"{request.method} {request.url.path}"
        _request_count[key] += 1
        _latency_sum[key] += duration_ms
        if response.status_code >= 500:
            _error_count[key] += 1

        return response


def get_metrics() -> dict:
    """Return a snapshot of in-process request metrics."""
    return {
        key: {
            "request_count": _request_count[key],
            "error_count": _error_count.get(key, 0),
            "avg_latency_ms": round(_latency_sum[key] / _request_count[key], 1),
        }
        for key in _request_count
    }
