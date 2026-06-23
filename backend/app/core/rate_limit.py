from collections import defaultdict, deque
from time import monotonic

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


AUTH_ROUTE_PREFIXES = (
    "/auth",
    "/login",
    "/registro",
    "/signup",
    "/signin",
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        request_limit: int,
        request_window_seconds: int,
        auth_attempt_limit: int,
        auth_window_seconds: int,
        max_request_bytes: int,
    ):
        super().__init__(app)
        self.request_limit = request_limit
        self.request_window_seconds = request_window_seconds
        self.auth_attempt_limit = auth_attempt_limit
        self.auth_window_seconds = auth_window_seconds
        self.max_request_bytes = max_request_bytes
        self._requests = defaultdict(deque)
        self._auth_attempts = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        size_error = self._validate_content_length(request)
        if size_error is not None:
            return size_error

        client_id = self._client_id(request)
        route_key = self._route_key(request)
        now = monotonic()

        exceeded = self._is_limited(
            self._requests[(client_id, "all")],
            self.request_limit,
            self.request_window_seconds,
            now,
        )
        if exceeded:
            return self._rate_limit_response(self.request_window_seconds)

        if self._is_auth_route(route_key):
            exceeded = self._is_limited(
                self._auth_attempts[(client_id, route_key)],
                self.auth_attempt_limit,
                self.auth_window_seconds,
                now,
            )
            if exceeded:
                return self._rate_limit_response(self.auth_window_seconds)

        return await call_next(request)

    def _validate_content_length(self, request: Request):
        raw_length = request.headers.get("content-length")
        if raw_length is None:
            return None

        try:
            content_length = int(raw_length)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Content-Length invalido"},
            )

        if content_length > self.max_request_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "El payload supera el limite permitido"},
            )
        return None

    def _client_id(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _route_key(self, request: Request) -> str:
        return request.url.path.rstrip("/") or "/"

    def _is_auth_route(self, route_key: str) -> bool:
        return route_key.startswith(AUTH_ROUTE_PREFIXES)

    def _is_limited(
        self,
        attempts,
        limit: int,
        window_seconds: int,
        now: float,
    ) -> bool:
        cutoff = now - window_seconds
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()

        if len(attempts) >= limit:
            return True

        attempts.append(now)
        return False

    def _rate_limit_response(self, retry_after_seconds: int):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Demasiadas solicitudes. Intenta nuevamente mas tarde",
            },
            headers={"Retry-After": str(retry_after_seconds)},
        )
