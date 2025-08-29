from __future__ import annotations
import time
from collections import defaultdict, deque
from typing import Deque

# Requests allowed per window
RATE_LIMIT = 60       # e.g. 60 requests
WINDOW_SIZE = 60.0    # in seconds

# Storage: per IP → deque of timestamps
_requests: dict[str, Deque[float]] = defaultdict(deque)


def is_allowed(ip: str, limit: int = RATE_LIMIT, window: float = WINDOW_SIZE) -> tuple[bool, int]:
    """
    Returns (allowed, remaining).
    - allowed = True if under limit
    - remaining = requests left in window
    """
    now = time.time()
    q = _requests[ip]

    # Drop timestamps older than the window
    while q and now - q[0] > window:
        q.popleft()

    if len(q) < limit:
        q.append(now)
        return True, limit - len(q)
    else:
        return False, 0
