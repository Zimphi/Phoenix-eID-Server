"""Small typed model of the mandatory national TR-03130 SOAP profile."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType

from .constants import ATTRIBUTE_NAMES, EID_TYPES, LOA_ORDER


class AttributeRequest(StrEnum):
    ALLOWED = "ALLOWED"
    PROHIBITED = "PROHIBITED"
    REQUIRED = "REQUIRED"


class AttributeResponse(StrEnum):
    ALLOWED = "ALLOWED"
    PROHIBITED = "PROHIBITED"
    NOT_ON_CHIP = "NOTONCHIP"


class EIDTypeSelection(StrEnum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"


@dataclass(frozen=True, slots=True)
class UseIDRequest:
    operations: Mapping[str, AttributeRequest]
    age: int | None = None
    community_id: str | None = None
    transaction_info: str | None = None
    loa: str | None = None
    eid_types: Mapping[str, EIDTypeSelection] = field(default_factory=dict)
    supplied_psk_id: str | None = None
    supplied_psk: bytes | None = None

    def __post_init__(self) -> None:
        unknown = set(self.operations) - set(ATTRIBUTE_NAMES)
        if unknown:
            raise ValueError(f"unknown operations: {sorted(unknown)}")
        unknown_types = set(self.eid_types) - set(EID_TYPES)
        if unknown_types:
            raise ValueError(f"unknown eID types: {sorted(unknown_types)}")
        if self.loa is not None and self.loa not in LOA_ORDER:
            raise ValueError("unsupported level of assurance")
        if self.age is not None and not 0 <= self.age <= 150:
            raise ValueError("age must be between 0 and 150")
        if self.community_id is not None:
            value = self.community_id
            if not value.isascii() or not value.isdigit() or len(value) > 32:
                raise ValueError("CommunityID must contain at most 32 ASCII digits")
        if bool(self.supplied_psk_id) != (self.supplied_psk is not None):
            raise ValueError("PSK ID and key must be supplied together")
        object.__setattr__(self, "operations", MappingProxyType(dict(self.operations)))
        object.__setattr__(self, "eid_types", MappingProxyType(dict(self.eid_types)))


@dataclass(frozen=True, slots=True)
class AuthenticationResult:
    personal_data: Mapping[str, object]
    operations: Mapping[str, AttributeResponse]
    document_valid: bool
    fulfils_age: bool | None = None
    fulfils_place: bool | None = None
    loa: str | None = None
    eid_type: str | None = None
    completed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if set(self.operations) - set(ATTRIBUTE_NAMES):
            raise ValueError("result contains unknown operations")
        if set(self.personal_data) - set(ATTRIBUTE_NAMES):
            raise ValueError("result contains unknown personal data")
        if set(self.personal_data) - {
            name for name, status in self.operations.items() if status == AttributeResponse.ALLOWED
        }:
            raise ValueError("result contains personal data without effective authorization")
        if self.loa is not None and self.loa not in LOA_ORDER:
            raise ValueError("unsupported result level of assurance")
        if self.eid_type is not None and self.eid_type not in EID_TYPES:
            raise ValueError("unsupported result eID type")
        object.__setattr__(self, "personal_data", MappingProxyType(dict(self.personal_data)))
        object.__setattr__(self, "operations", MappingProxyType(dict(self.operations)))
