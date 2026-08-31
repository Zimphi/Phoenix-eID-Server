"""Fail-closed service configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .constants import ATTRIBUTE_NAMES


def _https_url(value: str, name: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"{name} must be an absolute HTTPS URL without userinfo")
    return value


@dataclass(frozen=True, slots=True)
class ServiceProvider:
    identifier: str
    refresh_url: str
    communication_error_url: str | None = None
    terminal_rights: frozenset[str] = field(default_factory=lambda: frozenset(ATTRIBUTE_NAMES))
    max_sessions: int = 32

    def __post_init__(self) -> None:
        if not self.identifier or len(self.identifier) > 256:
            raise ValueError("invalid service provider identifier")
        _https_url(self.refresh_url, "refresh_url")
        if self.communication_error_url:
            _https_url(self.communication_error_url, "communication_error_url")
        if set(self.terminal_rights) - set(ATTRIBUTE_NAMES):
            raise ValueError("unknown terminal right")
        if not 1 <= self.max_sessions <= 100_000:
            raise ValueError("max_sessions is out of range")


@dataclass(frozen=True, slots=True)
class ServerConfig:
    ecard_server_url: str
    providers: dict[str, ServiceProvider]
    session_ttl_seconds: int = 300
    token_ttl_seconds: int = 120
    psk_bytes: int = 32
    max_xml_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        _https_url(self.ecard_server_url, "ecard_server_url")
        if not 30 <= self.session_ttl_seconds <= 3600:
            raise ValueError("session TTL must be between 30 and 3600 seconds")
        if not 10 <= self.token_ttl_seconds <= self.session_ttl_seconds:
            raise ValueError("token TTL must be between 10 seconds and the session TTL")
        if self.psk_bytes < 32:
            raise ValueError("PSKs must provide at least 256 bits")
        if not 4096 <= self.max_xml_bytes <= 16 * 1024 * 1024:
            raise ValueError("max_xml_bytes is out of range")
