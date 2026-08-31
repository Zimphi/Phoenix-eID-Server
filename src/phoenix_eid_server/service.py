"""TR-03130 application service independent of XML and transport frameworks."""

from __future__ import annotations

from dataclasses import dataclass

from .config import ServerConfig, ServiceProvider
from .errors import EIDError, get_result, use_id
from .models import AttributeRequest, AuthenticationResult, EIDTypeSelection, UseIDRequest
from .sessions import Session, SessionStore


@dataclass(frozen=True, slots=True)
class ServerInfo:
    version_string: str
    major: int
    minor: int
    bugfix: int
    rights: frozenset[str]


class EIDService:
    def __init__(self, config: ServerConfig, sessions: SessionStore | None = None):
        self.config = config
        self.sessions = sessions or SessionStore(
            config.session_ttl_seconds, config.token_ttl_seconds, config.psk_bytes
        )

    def provider(self, provider_id: str) -> ServiceProvider:
        try:
            return self.config.providers[provider_id]
        except KeyError as exc:
            raise PermissionError("unknown service provider") from exc

    def use_id(self, provider_id: str, request: UseIDRequest) -> Session:
        provider = self.provider(provider_id)
        selected = {
            name
            for name, choice in request.operations.items()
            if choice != AttributeRequest.PROHIBITED
        }
        if not selected:
            raise use_id("missingArgument", "at least one operation must be selected")
        if "AgeVerification" in selected and request.age is None:
            raise use_id("missingArgument", "AgeVerificationRequest is required")
        if "PlaceVerification" in selected and request.community_id is None:
            raise use_id("missingArgument", "PlaceVerificationRequest is required")
        missing = selected - provider.terminal_rights
        required_missing = {
            name for name in missing if request.operations[name] == AttributeRequest.REQUIRED
        }
        if required_missing:
            raise use_id(
                "missingTerminalRights",
                f"terminal certificate lacks required rights: {sorted(required_missing)}",
            )
        return self.sessions.create(provider_id, request, provider.max_sessions)

    def get_result(self, provider_id: str, session_id: str, counter: int) -> AuthenticationResult:
        session = self.sessions.get_result(provider_id, session_id, counter)
        if session.error:
            if isinstance(session.error, EIDError):
                raise session.error
            raise get_result("invalidDocument", "authentication or document validation failed")
        if session.result is None:
            raise get_result("invalidDocument", "session completed without a validated result")
        self._validate_result_policy(session.request, session.result)
        return session.result

    def get_server_info(self, provider_id: str) -> ServerInfo:
        provider = self.provider(provider_id)
        return ServerInfo("TR-03130 eID-Interface 2.4.0", 2, 4, 0, provider.terminal_rights)

    @staticmethod
    def _validate_result_policy(request: UseIDRequest, result: AuthenticationResult) -> None:
        if not result.document_valid:
            raise get_result("invalidDocument", "document validation failed")
        if request.eid_types and result.eid_type:
            selection = request.eid_types.get(result.eid_type)
            if selection == EIDTypeSelection.DENIED:
                raise get_result("deniedDocument", "the used eID type was explicitly denied")
        if request.loa and result.loa:
            from .constants import LOA_ORDER

            explicitly_allowed = (
                result.eid_type is not None
                and request.eid_types.get(result.eid_type) == EIDTypeSelection.ALLOWED
            )
            if LOA_ORDER[result.loa] < LOA_ORDER[request.loa] and not explicitly_allowed:
                raise get_result("deniedDocument", "the used eID type has insufficient assurance")
