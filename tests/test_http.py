from phoenix_eid_server.http import HTTPApplication
from phoenix_eid_server.message_security import MessageSecurity


class PassThroughSecurity(MessageSecurity):
    def verify(self, provider_id, document):
        return document

    def sign(self, provider_id, document):
        return document


def test_soap_route_fails_closed_without_message_security(service):
    app = HTTPApplication(service)
    response = app.handle(
        "POST",
        "/eid",
        {"content-type": "text/xml"},
        b"<not-important/>",
        provider_id="provider-a",
    )
    assert response.status == 503


def test_unknown_mtls_provider_is_denied_before_xml_processing(service):
    app = HTTPApplication(service, message_security=PassThroughSecurity())
    response = app.handle(
        "POST",
        "/eid",
        {"content-type": "text/xml"},
        b"<not-important/>",
        provider_id="unknown",
    )
    assert response.status == 403


def test_token_endpoint_is_no_store_and_one_time(service):
    from phoenix_eid_server.models import AttributeRequest, UseIDRequest

    session = service.use_id("provider-a", UseIDRequest({"GivenNames": AttributeRequest.REQUIRED}))
    app = HTTPApplication(service)
    first = app.handle("GET", f"/tctoken/{session.identifier}", {}, b"")
    second = app.handle("GET", f"/tctoken/{session.identifier}", {}, b"")
    assert first.status == 200
    assert first.content_type == "text/xml; charset=utf-8"
    assert ("Cache-Control", "no-store") in first.headers
    assert second.status == 404


def test_paos_requires_actual_psk_listener_authentication(service):
    app = HTTPApplication(service)
    response = app.handle(
        "POST",
        "/ecard",
        {"content-type": "application/vnd.paos+xml", "requestid": "anything"},
        b"<x/>",
        psk_authenticated=False,
    )
    assert response.status == 401
