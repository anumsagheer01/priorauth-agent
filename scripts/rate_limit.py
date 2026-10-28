"""Bounded 429 handling for cloud eval scripts. No model call here.

Why this exists: on 2026-10-27 the full 30-case eval aborted on a
429 RESOURCE_EXHAUSTED with no results_real.json written, because
scripts/evaluate_real.py had no sleep, retry, exception, or 429
handling at all. A single quota error therefore destroyed the
whole run's output.

Rules, enforced here and in both eval scripts:
- Detect a 429 by exception class name, a numeric code/status
  attribute, or the strings "429" / "RESOURCE_EXHAUSTED" in the
  message. Vertex / ADK / google-api-core surface the same
  condition in different exception types, so no single class
  is trusted alone.
- Retry the affected case only, a bounded number of times, with
  increasing delays (10s, 20s, 40s by default). Never retry in a
  tight loop, and never retry indefinitely.
- If the case still fails after the bounded retries, the caller
  records it as not completed, with its error, continues with
  the remaining cases, and writes partial results whose
  denominators say exactly how many cases completed and how
  many did not. Failed cases are never given invented results,
  and metrics are computed only over completed cases, labeled
  as such.
- A 429 is a rate-limit stop for that case, not a reason to
  change the model, region, budget, or cap inside the eval.
"""

from __future__ import annotations

import time

# Attempts after the first try: 3 retries, 4 attempts total.
DEFAULT_MAX_RETRIES = 3
# Increasing backoff between retries. Not a tight loop.
DEFAULT_RETRY_DELAYS_SECONDS = (10.0, 20.0, 40.0)


def is_rate_limit_error(exc: BaseException) -> bool:
    """Return True if exc looks like a 429 / RESOURCE_EXHAUSTED error."""
    name = type(exc).__name__
    if name in ("ResourceExhausted", "TooManyRequests", "RateLimitError",
                "RateLimitExceeded"):
        return True
    for attr in ("code", "status_code", "status"):
        try:
            value = getattr(exc, attr, None)
        except Exception:
            value = None
        if value in (429, "429", "RESOURCE_EXHAUSTED"):
            return True
        if isinstance(value, str) and "RESOURCE_EXHAUSTED" in value:
            return True
    text = str(exc)
    return "429" in text or "RESOURCE_EXHAUSTED" in text


def call_with_429_retry(fn, max_retries: int = DEFAULT_MAX_RETRIES,
                        delays: tuple[float, ...] = DEFAULT_RETRY_DELAYS_SECONDS,
                        sleep_fn=time.sleep):
    """Call fn, retrying only 429 errors a bounded number of times.

    Returns fn()'s result on success. Re-raises the last error if
    it is not a 429, or if the retry budget is exhausted. sleep_fn
    is injectable so tests never wait for real backoff delays.
    """
    last_exc: BaseException | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - re-raised unless 429
            last_exc = exc
            if not is_rate_limit_error(exc):
                raise
            if attempt >= max_retries:
                raise
            delay = delays[attempt] if attempt < len(delays) else delays[-1]
            sleep_fn(delay)
    # Unreachable in practice: the loop either returns or raises.
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("call_with_429_retry exited without a result or an error")
