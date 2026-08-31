from xml.etree import ElementTree as ET

from phoenix_eid_server.constants import PAOS_BINDING, PSK_PROTOCOL
from phoenix_eid_server.models import AttributeRequest, UseIDRequest
from phoenix_eid_server.tctoken import render_tc_token


def test_tc_token_has_normative_order_and_values(service):
    session = service.use_id("provider-a", UseIDRequest({"GivenNames": AttributeRequest.REQUIRED}))
    provider = service.provider("provider-a")
    data = render_tc_token(
        session,
        service.config.ecard_server_url,
        provider.refresh_url,
        provider.communication_error_url,
    )
    root = ET.fromstring(data)
    assert [child.tag for child in root] == [
        "ServerAddress",
        "SessionIdentifier",
        "RefreshAddress",
        "CommunicationErrorAddress",
        "Binding",
        "PathSecurity-Protocol",
        "PathSecurity-Parameters",
    ]
    assert root.findtext("ServerAddress") == service.config.ecard_server_url
    assert root.findtext("SessionIdentifier") == session.psk_id
    assert root.findtext("Binding") == PAOS_BINDING
    assert root.findtext("PathSecurity-Protocol") == PSK_PROTOCOL
    assert bytes.fromhex(root.findtext("PathSecurity-Parameters/PSK")) == bytes(session.psk)
