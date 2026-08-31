from xml.etree import ElementTree as ET

from phoenix_eid_server.constants import DSS_NS, EID_NS, RESULT_MAJOR_OK, SOAP_NS
from phoenix_eid_server.models import AttributeResponse, AuthenticationResult
from phoenix_eid_server.soap import SoapEndpoint


def envelope(payload: str) -> bytes:
    return f'''<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:eid="{EID_NS}">
      <soap:Header/><soap:Body>{payload}</soap:Body></soap:Envelope>'''.encode()


def find(root, namespace, name):
    return root.find(f".//{{{namespace}}}{name}")


def test_use_id_and_get_result_round_trip(service):
    endpoint = SoapEndpoint(service)
    response = endpoint.dispatch(
        "provider-a",
        envelope(
            """<eid:useIDRequest><eid:UseOperations>
              <eid:GivenNames>REQUIRED</eid:GivenNames>
              <eid:FamilyNames>ALLOWED</eid:FamilyNames>
            </eid:UseOperations></eid:useIDRequest>"""
        ),
    )
    root = ET.fromstring(response)
    assert find(root, DSS_NS, "ResultMajor").text == RESULT_MAJOR_OK
    session_id = find(root, EID_NS, "ID").text
    session = service.sessions._sessions[session_id]
    service.sessions.complete(
        session_id,
        AuthenticationResult(
            personal_data={"GivenNames": "ERIKA", "FamilyNames": "MUSTERMANN"},
            operations={
                "GivenNames": AttributeResponse.ALLOWED,
                "FamilyNames": AttributeResponse.ALLOWED,
            },
            document_valid=True,
        ),
    )
    result_response = endpoint.dispatch(
        "provider-a",
        envelope(
            f"""<eid:getResultRequest><eid:Session><eid:ID>{session_id}</eid:ID>
              </eid:Session><eid:RequestCounter>1</eid:RequestCounter></eid:getResultRequest>"""
        ),
    )
    result_root = ET.fromstring(result_response)
    assert find(result_root, EID_NS, "GivenNames").text == "ERIKA"
    assert find(result_root, EID_NS, "FamilyNames").text == "MUSTERMANN"
    assert session.psk == bytearray()
    assert session_id not in service.sessions._sessions


def test_no_result_yet_does_not_consume_session(service):
    endpoint = SoapEndpoint(service)
    created = endpoint.dispatch(
        "provider-a",
        envelope(
            "<eid:useIDRequest><eid:UseOperations><eid:GivenNames>REQUIRED</eid:GivenNames>"
            "</eid:UseOperations></eid:useIDRequest>"
        ),
    )
    session_id = find(ET.fromstring(created), EID_NS, "ID").text
    pending = endpoint.dispatch(
        "provider-a",
        envelope(
            f"<eid:getResultRequest><eid:Session><eid:ID>{session_id}</eid:ID></eid:Session>"
            "<eid:RequestCounter>1</eid:RequestCounter></eid:getResultRequest>"
        ),
    )
    assert find(ET.fromstring(pending), DSS_NS, "ResultMinor").text.endswith(
        "/getResult#noResultYet"
    )
    assert session_id in service.sessions._sessions


def test_dtd_is_rejected(service):
    endpoint = SoapEndpoint(service)
    result = endpoint.dispatch("provider-a", b'<!DOCTYPE x [<!ENTITY a "x">]><x/>')
    assert find(ET.fromstring(result), DSS_NS, "ResultMinor").text.endswith(
        "/common#schemaViolation"
    )
