"""Bounded, expiring, one-time session storage for TR-03130."""

from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from .errors import get_result, use_id
from .models import AuthenticationResult, UseIDRequest


class SessionState(StrEnum):
    OPEN = "OPEN"
    EAC_ACTIVE = "EAC_ACTIVE"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass(slots=True)
class Session:
    identifier: str
    psk_id: str
    psk: bytearray
    token_handle: str
    provider_id: str
    request: UseIDRequest
    created_at: datetime
    expires_at: datetime
    token_expires_at: datetime
    state: SessionState = SessionState.OPEN
    last_counter: int = 0
    result: AuthenticationResult | None = None
    error: Exception | None = None
    token_retrieved: bool = False
    context: dict[str, object] = field(default_factory=dict)

    def destroy(self, *, drop_result: bool = True) -> None:
        self.psk[:] = b"\0" * len(self.psk)
        self.psk.clear()
        self.context.clear()
        if drop_result:
            self.result = None


class SessionStore:
    def __init__(self, ttl_seconds: int, token_ttl_seconds: int, psk_bytes: int = 32):
        self._ttl = ttl_seconds
        self._token_ttl = token_ttl_seconds
        self._psk_bytes = psk_bytes
        self._sessions: dict[str, Session] = {}
        self._tokens: dict[str, str] = {}
        self._psk_ids: dict[str, str] = {}
        self._lock = threading.RLock()

    def create(self, provider_id: str, request: UseIDRequest, maximum: int) -> Session:
        now = datetime.now(UTC)
        with self._lock:
            self._purge(now)
            if sum(s.provider_id == provider_id for s in self._sessions.values()) >= maximum:
                raise use_id("tooManyOpenSessions", "maximum number of sessions reached")
            session_id = self._unique_hex(self._sessions, 16)
            psk_id = request.supplied_psk_id or self._unique_hex(self._psk_ids, 16)
            if psk_id in self._psk_ids:
                raise use_id("invalidPSK", "PSK identity is already in use")
            key = request.supplied_psk or secrets.token_bytes(self._psk_bytes)
            if len(key) < 32 or len(key) > 256:
                raise use_id("invalidPSK", "PSK length is outside the supported range")
            # The eService knows the random Session.ID from useID and can form
            # /tctoken/{Session.ID} without a non-standard SOAP return value.
            handle = session_id
            session = Session(
                identifier=session_id,
                psk_id=psk_id,
                psk=bytearray(key),
                token_handle=handle,
                provider_id=provider_id,
                request=request,
                created_at=now,
                expires_at=now + timedelta(seconds=self._ttl),
                token_expires_at=now + timedelta(seconds=self._token_ttl),
            )
            self._sessions[session_id] = session
            self._tokens[handle] = session_id
            self._psk_ids[psk_id] = session_id
            return session

    def by_token(self, handle: str, consume: bool = True) -> Session:
        now = datetime.now(UTC)
        with self._lock:
            self._purge(now)
            identifier = self._tokens.get(handle)
            session = self._sessions.get(identifier or "")
            if session is None or session.token_expires_at <= now:
                raise KeyError("unknown or expired token")
            if consume and session.token_retrieved:
                raise KeyError("token was already retrieved")
            if consume:
                session.token_retrieved = True
                self._tokens.pop(handle, None)
            return session

    def by_psk_identity(self, identity: str) -> Session | None:
        now = datetime.now(UTC)
        with self._lock:
            self._purge(now)
            session = self._sessions.get(self._psk_ids.get(identity, ""))
            if session is None or session.state not in {SessionState.OPEN, SessionState.EAC_ACTIVE}:
                return None
            return session

    def get_result(self, provider_id: str, identifier: str, counter: int) -> Session:
        now = datetime.now(UTC)
        with self._lock:
            self._purge(now)
            session = self._sessions.get(identifier)
            if session is None or session.provider_id != provider_id:
                raise get_result("invalidSession", "unknown, expired, or foreign session")
            if counter <= 0 or counter <= session.last_counter:
                self._remove(session)
                raise get_result("invalidCounter", "RequestCounter must increase monotonically")
            session.last_counter = counter
            if session.state in {SessionState.OPEN, SessionState.EAC_ACTIVE}:
                raise get_result("noResultYet", "authentication has not completed")
            self._remove(session, drop_result=False)
            return session

    def complete(self, identifier: str, result: AuthenticationResult) -> None:
        with self._lock:
            session = self._sessions.get(identifier)
            if session is None or session.state not in {SessionState.OPEN, SessionState.EAC_ACTIVE}:
                raise KeyError("session cannot be completed")
            session.result = result
            session.state = SessionState.COMPLETE

    def fail(self, identifier: str, error: Exception) -> None:
        with self._lock:
            session = self._sessions.get(identifier)
            if session is None or session.state not in {SessionState.OPEN, SessionState.EAC_ACTIVE}:
                raise KeyError("session cannot be failed")
            session.error = error
            session.state = SessionState.FAILED

    def _remove(self, session: Session, *, drop_result: bool = True) -> None:
        self._sessions.pop(session.identifier, None)
        self._tokens.pop(session.token_handle, None)
        self._psk_ids.pop(session.psk_id, None)
        session.destroy(drop_result=drop_result)

    def _purge(self, now: datetime) -> None:
        for session in list(self._sessions.values()):
            if session.expires_at <= now:
                self._remove(session)

    @staticmethod
    def _unique_hex(index: dict[str, object], byte_count: int) -> str:
        while True:
            value = secrets.token_hex(byte_count)
            if value not in index:
                return value
