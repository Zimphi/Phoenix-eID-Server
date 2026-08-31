"""WS-Security provider boundary for TR-03130-1 section 3.5.2."""

from __future__ import annotations

from abc import ABC, abstractmethod


class MessageSecurity(ABC):
    """Verify requests and sign responses using an approved XML-DSig implementation."""

    @abstractmethod
    def verify(self, provider_id: str, document: bytes) -> bytes:
        """Verify signature, certificate, algorithms, references, and freshness.

        Return the authenticated SOAP document. Implementations must reject wrapping,
        duplicate-ID, external-reference, SHA-1, and unsigned-body attacks.
        """

    @abstractmethod
    def sign(self, provider_id: str, document: bytes) -> bytes:
        """Apply the configured RecipientToken XML signature to the SOAP response."""
