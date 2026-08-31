"""Fail-closed boundary between PAOS/EAC2 processing and the eID service core.

The boundary is intentionally evidence based: no backend can publish identity data
unless it attests all four document-validity checks required by TR-03130-1 2.4.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from .constants import ATTRIBUTE_NAMES
from .errors import get_result
from .models import AttributeRequest, AttributeResponse, AuthenticationResult
from .sessions import Session


@dataclass(frozen=True, slots=True)
class DocumentEvidence:
    chip_authentication: bool
    passive_authentication: bool
    validity_date_checked: bool
    blacklist_checked: bool
    expired: bool
    revoked: bool
    reference_date: date

    @property
    def valid(self) -> bool:
        return (
            self.chip_authentication
            and self.passive_authentication
            and self.validity_date_checked
            and self.blacklist_checked
            and not self.expired
            and not self.revoked
        )


@dataclass(frozen=True, slots=True)
class EACOutcome:
    data: Mapping[str, object]
    user_authorized: frozenset[str]
    on_chip: frozenset[str]
    evidence: DocumentEvidence
    fulfils_age: bool | None = None
    fulfils_place: bool | None = None
    loa: str | None = None
    eid_type: str | None = None


class PAOSBackend(ABC):
    """Provider SPI for the TR-03112 PAOS/EAC command exchange."""

    @abstractmethod
    def exchange(self, session: Session, paos_message: bytes) -> bytes:
        """Validate one client response and return the next PAOS command."""

    @abstractmethod
    def outcome(self, session: Session) -> EACOutcome | None:
        """Return a final outcome once the EAC2 exchange has completed."""


def validated_result(session: Session, outcome: EACOutcome, terminal_rights: frozenset[str]):
    if not outcome.evidence.valid:
        raise get_result("invalidDocument", "the document validity verification failed")
    unknown = (set(outcome.data) | set(outcome.user_authorized) | set(outcome.on_chip)) - set(
        ATTRIBUTE_NAMES
    )
    if unknown:
        raise ValueError(f"EAC backend returned unknown attributes: {sorted(unknown)}")
    requested = {
        name
        for name, selection in session.request.operations.items()
        if selection != AttributeRequest.PROHIBITED
    }
    effective = requested & terminal_rights & outcome.user_authorized
    leaked = set(outcome.data) - effective
    if leaked:
        raise ValueError(f"EAC backend returned unauthorized attributes: {sorted(leaked)}")
    operations = {}
    for name in session.request.operations:
        if name in effective and name in outcome.on_chip:
            operations[name] = AttributeResponse.ALLOWED
        elif name in effective:
            operations[name] = AttributeResponse.NOT_ON_CHIP
        else:
            operations[name] = AttributeResponse.PROHIBITED
    required_unavailable = {
        name
        for name, selection in session.request.operations.items()
        if selection == AttributeRequest.REQUIRED
        and operations.get(name) != AttributeResponse.ALLOWED
    }
    if required_unavailable:
        raise get_result(
            "invalidDocument", f"required attributes unavailable: {sorted(required_unavailable)}"
        )
    return AuthenticationResult(
        personal_data={name: value for name, value in outcome.data.items() if name in effective},
        operations=operations,
        document_valid=True,
        fulfils_age=outcome.fulfils_age,
        fulfils_place=outcome.fulfils_place,
        loa=outcome.loa,
        eid_type=outcome.eid_type,
    )
