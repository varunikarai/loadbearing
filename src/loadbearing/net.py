"""One JSON request with retries, for Token Factory and Tavily.

A paid probe makes dozens of model calls after its forks have already run. One
rate limit, one 5xx or one dropped connection should cost a short wait, not the
whole run. Anything that will not get better by waiting, such as a bad key or a
bad request, fails at once.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable

RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_WAIT = 30.0  # seconds; a Retry-After longer than this is capped


def fetch_json(
    req: urllib.request.Request,
    timeout: float,
    tries: int = 4,
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    """The JSON reply to `req`. Waits 1, 2, then 4 seconds between tries, or what Retry-After asks."""
    for attempt in range(tries):
        last = attempt == tries - 1
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:  # before URLError, which it subclasses
            if exc.code not in RETRY_STATUS or last:
                raise
            wait = _retry_after(exc) or 2.0**attempt
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if last:
                raise
            wait = 2.0**attempt
        sleep(min(wait, MAX_WAIT))
    raise AssertionError("unreachable")


def _retry_after(exc: urllib.error.HTTPError) -> float | None:
    value = (exc.headers or {}).get("Retry-After")
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None  # an HTTP date; the plain backoff is close enough
