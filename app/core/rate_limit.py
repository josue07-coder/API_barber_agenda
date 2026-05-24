from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request, status

from app.core.config import settings


_login_attempts: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    _login_attempts.clear()


def check_login_rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    now = monotonic()
    window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    max_requests = settings.LOGIN_RATE_LIMIT_REQUESTS

    attempts = _login_attempts[client_host]
    while attempts and now - attempts[0] > window:
        attempts.popleft()

    if len(attempts) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intenta nuevamente mas tarde",
        )

    attempts.append(now)
