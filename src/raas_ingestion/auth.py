from dataclasses import dataclass
from typing import Callable, Optional
import time


@dataclass
class TokenState:
    access_token: str
    expires_at: float
    token_type: str = "Bearer"

    def is_expired(self, buffer_seconds: int = 60, now: Optional[float] = None) -> bool:
        current = time.time() if now is None else now
        return current >= (self.expires_at - buffer_seconds)


class TokenManager:
    """Manages Workday OAuth2 / ISU bearer tokens with proactive refresh."""

    def __init__(
        self,
        fetcher: Callable[[], TokenState],
        buffer_seconds: int = 60,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._fetcher = fetcher
        self._buffer_seconds = buffer_seconds
        self._clock = clock
        self._state: Optional[TokenState] = None

    def get_token(self, force_refresh: bool = False) -> str:
        now = self._clock()
        if force_refresh or self._state is None or self._state.is_expired(self._buffer_seconds, now=now):
            self._state = self._fetcher()
        return self._state.access_token

    def get_auth_header(self, force_refresh: bool = False) -> dict[str, str]:
        token = self.get_token(force_refresh=force_refresh)
        token_type = self._state.token_type if self._state else "Bearer"
        return {"Authorization": f"{token_type} {token}"}
