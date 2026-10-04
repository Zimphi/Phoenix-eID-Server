import re

import pytest

from phoenix_eid_server.errors import EIDError
from phoenix_eid_server.models import AttributeRequest, UseIDRequest


def request(**operations):
    return UseIDRequest({name: AttributeRequest(value) for name, value in operations.items()})


def test_session_ids_and_psk_are_random_and_sufficiently_long(service):
    first = service.use_id("provider-a", request(GivenNames="REQUIRED"))
    second = service.use_id("provider-a", request(FamilyNames="REQUIRED"))
    assert first.identifier != second.identifier
    assert re.fullmatch(r"[0-9a-f]{32}", first.identifier)
    assert re.fullmatch(r"[0-9a-f]{32}", first.psk_id)
    assert len(first.psk) == 32


def test_per_provider_session_limit(service):
    service.use_id("provider-a", request(GivenNames="REQUIRED"))
    service.use_id("provider-a", request(FamilyNames="REQUIRED"))
    with pytest.raises(EIDError, match="maximum") as raised:
        service.use_id("provider-a", request(GivenNames="REQUIRED"))
    assert raised.value.result_minor.endswith("/useID#tooManyOpenSessions")


def test_missing_required_terminal_right_is_rejected(service):
    with pytest.raises(EIDError) as raised:
        service.use_id("provider-a", request(Nationality="REQUIRED"))
    assert raised.value.result_minor.endswith("/useID#missingTerminalRights")


def test_verification_argument_is_required(service):
    with pytest.raises(EIDError) as raised:
        service.use_id("provider-a", request(AgeVerification="REQUIRED"))
    assert raised.value.result_minor.endswith("/useID#missingArgument")


def test_tc_token_handle_is_one_time(service):
    session = service.use_id("provider-a", request(GivenNames="REQUIRED"))
    assert service.sessions.by_token(session.token_handle) is session
    with pytest.raises(KeyError):
        service.sessions.by_token(session.token_handle)


def test_refresh_lookup_only_releases_completed_result(service):
    session = service.use_id("provider-a", request(GivenNames="REQUIRED"))
    address = f"https://service.example.test/refresh/{session.identifier}"
    service.sessions.configure_refresh_address(session.identifier, address)
    assert session.refresh_address == address
    with pytest.raises(KeyError):
        service.sessions.by_refresh_handle(session.identifier)


def test_invalid_counter_invalidates_session(service):
    session = service.use_id("provider-a", request(GivenNames="REQUIRED"))
    with pytest.raises(EIDError) as raised:
        service.get_result("provider-a", session.identifier, 0)
    assert raised.value.result_minor.endswith("/getResult#invalidCounter")
    assert session.identifier not in service.sessions._sessions
    assert session.psk == bytearray()
