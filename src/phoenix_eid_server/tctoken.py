"""Strict TC Token serializer for TR-03124-1 section 2.6."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from .constants import PAOS_BINDING, PSK_PROTOCOL
from .sessions import Session


def render_tc_token(
    session: Session,
    server_address: str,
    refresh_address: str,
    communication_error_address: str | None = None,
) -> bytes:
    """Return the required namespace-free XML fragment in normative element order."""
    root = ET.Element("TCTokenType")
    ET.SubElement(root, "ServerAddress").text = server_address
    ET.SubElement(root, "SessionIdentifier").text = session.psk_id
    ET.SubElement(root, "RefreshAddress").text = refresh_address
    if communication_error_address:
        ET.SubElement(root, "CommunicationErrorAddress").text = communication_error_address
    ET.SubElement(root, "Binding").text = PAOS_BINDING
    ET.SubElement(root, "PathSecurity-Protocol").text = PSK_PROTOCOL
    parameters = ET.SubElement(root, "PathSecurity-Parameters")
    ET.SubElement(parameters, "PSK").text = bytes(session.psk).hex().upper()
    return ET.tostring(root, encoding="utf-8", short_empty_elements=False)
