from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from time import monotonic


@dataclass
class SessionEntry:
    value: dict
    expires_at: float


class SessionStore:
    def __init__(self, max_sessions: int, ttl_seconds: int):
        self._max_sessions = max_sessions
        self._ttl_seconds = ttl_seconds
        self._entries: OrderedDict[str, SessionEntry] = OrderedDict()
        self._lock = Lock()

    def get(self, session_id: str) -> dict | None:
        with self._lock:
            self._remove_expired()
            entry = self._entries.get(session_id)
            if entry is None:
                return None
            self._entries.move_to_end(session_id)
            entry.expires_at = monotonic() + self._ttl_seconds
            return entry.value

    def set(self, session_id: str, value: dict) -> None:
        with self._lock:
            self._remove_expired()
            self._entries[session_id] = SessionEntry(
                value=value,
                expires_at=monotonic() + self._ttl_seconds,
            )
            self._entries.move_to_end(session_id)
            while len(self._entries) > self._max_sessions:
                self._entries.popitem(last=False)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._entries.pop(session_id, None) is not None

    def _remove_expired(self) -> None:
        now = monotonic()
        expired = [
            session_id
            for session_id, entry in self._entries.items()
            if entry.expires_at <= now
        ]
        for session_id in expired:
            del self._entries[session_id]
