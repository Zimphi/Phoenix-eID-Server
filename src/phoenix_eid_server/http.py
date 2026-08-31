"""Framework-neutral HTTP routing for SOAP, TC Token, and PAOS endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import unquote, urlsplit

from .eac import PAOSBackend, validated_result
from .errors import common
from .message_security import MessageSecurity
from .service import EIDService
from .soap import SoapEndpoint
from .tctoken import render_tc_token


@dataclass(frozen=True, slots=True)
class Response:
    status: int
    content_type: str
    body: bytes
    headers: tuple[tuple[str, str], ...] = ()


class HTTPApplication:
    def __init__(
        self,
        service: EIDService,
        paos: PAOSBackend | None = None,
        message_security: MessageSecurity | None = None,
    ):
        self.service = service
        self.soap = SoapEndpoint(service)
        self.paos = paos
        self.message_security = message_security

    def handle(
        self,
        method: str,
        target: str,
        headers: dict[str, str],
        body: bytes,
        *,
        provider_id: str | None = None,
        psk_authenticated: bool = False,
    ) -> Response:
        path = urlsplit(target).path
        if path == "/health" and method == "GET":
            return Response(200, "application/json", b'{"status":"ok"}')
        if path == "/eid" and method == "POST":
            if provider_id is None:
                return self._problem(401, "mutual TLS client authentication required")
            try:
                self.service.provider(provider_id)
            except PermissionError:
                return self._problem(403, "service provider is not authorized")
            if self.message_security is None:
                return self._problem(503, "no WS-Security backend configured")
            if headers.get("content-type", "").split(";", 1)[0].strip() not in {
                "text/xml",
                "application/soap+xml",
            }:
                return self._problem(415, "SOAP XML content type required")
            try:
                verified = self.message_security.verify(provider_id, body)
                response = self.soap.dispatch(provider_id, verified)
                signed = self.message_security.sign(provider_id, response)
            except Exception:
                # TR-03130 requires invalid signatures to map to internalError. The
                # transport deliberately returns no diagnostic signature details.
                response = self.soap._envelope(
                    self.soap._error(
                        "ErrorResponse",
                        common("internalError", "message security validation failed"),
                    )
                )
                try:
                    response = self.message_security.sign(provider_id, response)
                except Exception:
                    return self._problem(500, "message security response signing failed")
                return Response(400, "text/xml; charset=utf-8", response)
            return Response(200, "text/xml; charset=utf-8", signed)
        prefix = "/tctoken/"
        if path.startswith(prefix) and method == "GET":
            handle = unquote(path[len(prefix) :])
            try:
                session = self.service.sessions.by_token(handle)
                provider = self.service.provider(session.provider_id)
            except (KeyError, PermissionError):
                return self._problem(404, "unknown or expired token")
            token = render_tc_token(
                session,
                self.service.config.ecard_server_url,
                provider.refresh_url,
                provider.communication_error_url,
            )
            return Response(
                200,
                "text/xml; charset=utf-8",
                token,
                (("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )
        if path == "/ecard" and method == "POST":
            if not psk_authenticated:
                return self._problem(401, "TLS-PSK authentication required")
            if self.paos is None:
                return self._problem(503, "no PAOS/EAC backend configured")
            identity = headers.get("requestid", "")
            session = self.service.sessions.by_psk_identity(identity)
            if session is None:
                return self._problem(401, "unknown PSK identity")
            if headers.get("content-type", "").split(";", 1)[0].strip() != (
                "application/vnd.paos+xml"
            ):
                return self._problem(415, "PAOS content type required")
            try:
                response = self.paos.exchange(session, body)
                outcome = self.paos.outcome(session)
                if outcome is not None:
                    provider = self.service.provider(session.provider_id)
                    self.service.sessions.complete(
                        session.identifier,
                        validated_result(session, outcome, provider.terminal_rights),
                    )
            except Exception as exc:
                self.service.sessions.fail(session.identifier, exc)
                return self._problem(400, "invalid PAOS/EAC exchange")
            return Response(200, "application/vnd.paos+xml; charset=utf-8", response)
        return self._problem(404, "endpoint not found")

    @staticmethod
    def _problem(status: int, message: str) -> Response:
        safe = message.replace("\\", "\\\\").replace('"', '\\"')
        return Response(status, "application/problem+json", f'{{"detail":"{safe}"}}'.encode())
