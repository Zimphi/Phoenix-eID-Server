"""TLS context factories for the separated eService and eCard interfaces."""

from __future__ import annotations

import ssl
from collections.abc import Callable


def service_context(certfile: str, keyfile: str, client_ca: str) -> ssl.SSLContext:
    context = public_context(certfile, keyfile)
    context.load_verify_locations(cafile=client_ca)
    context.verify_mode = ssl.CERT_REQUIRED
    context.options |= ssl.OP_NO_COMPRESSION
    return context


def public_context(certfile: str, keyfile: str) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
    context.load_cert_chain(certfile, keyfile)
    context.set_ciphers("ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256")
    context.options |= ssl.OP_NO_COMPRESSION
    return context


def psk_context(
    certfile: str,
    keyfile: str,
    resolver: Callable[[str], bytes | None],
) -> ssl.SSLContext:
    if not hasattr(ssl.SSLContext, "set_psk_server_callback"):
        raise RuntimeError("this Python/OpenSSL build does not expose TLS-PSK callbacks")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.maximum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile, keyfile)
    # TR-03130-1 mandates the legacy AES-256 suite. Current TR-03116-4 also
    # mandates the SHA-256 AES-128 RSA-PSK suite; no unrelated TLS 1.2 suite
    # is enabled on this dedicated TLS-2 listener.
    context.set_ciphers("RSA-PSK-AES128-CBC-SHA256:RSA-PSK-AES256-CBC-SHA")
    context.options |= ssl.OP_NO_COMPRESSION

    def callback(identity: str | None) -> bytes:
        if not identity:
            return b""
        key = resolver(identity)
        return key or b""

    context.set_psk_server_callback(callback)
    return context
