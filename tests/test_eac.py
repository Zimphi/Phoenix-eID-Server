from datetime import date

import pytest

from phoenix_eid_server.eac import DocumentEvidence, EACOutcome, validated_result
from phoenix_eid_server.models import AttributeRequest, UseIDRequest


def evidence(**overrides):
    values = dict(
        chip_authentication=True,
        passive_authentication=True,
        validity_date_checked=True,
        blacklist_checked=True,
        expired=False,
        revoked=False,
        reference_date=date.today(),
    )
    values.update(overrides)
    return DocumentEvidence(**values)


def test_backend_cannot_release_unrequested_data(service):
    session = service.use_id("provider-a", UseIDRequest({"GivenNames": AttributeRequest.REQUIRED}))
    outcome = EACOutcome(
        data={"GivenNames": "ERIKA", "FamilyNames": "MUSTERMANN"},
        user_authorized=frozenset({"GivenNames", "FamilyNames"}),
        on_chip=frozenset({"GivenNames", "FamilyNames"}),
        evidence=evidence(),
    )
    with pytest.raises(ValueError, match="unauthorized"):
        validated_result(session, outcome, service.provider("provider-a").terminal_rights)


def test_age_verification_is_returned_without_disclosing_date_of_birth(service):
    session = service.use_id(
        "provider-a", UseIDRequest({"AgeVerification": AttributeRequest.REQUIRED}, age=18)
    )
    outcome = EACOutcome(
        data={},
        user_authorized=frozenset(),
        on_chip=frozenset(),
        evidence=evidence(),
        fulfils_age=True,
    )

    result = validated_result(session, outcome, service.provider("provider-a").terminal_rights)

    assert result.fulfils_age is True
    assert result.personal_data == {}
    assert result.operations["AgeVerification"] == "ALLOWED"


def test_backend_cannot_release_unrequested_age_verification(service):
    session = service.use_id(
        "provider-a", UseIDRequest({"GivenNames": AttributeRequest.REQUIRED})
    )
    outcome = EACOutcome(
        data={"GivenNames": "ERIKA"},
        user_authorized=frozenset({"GivenNames"}),
        on_chip=frozenset({"GivenNames"}),
        evidence=evidence(),
        fulfils_age=True,
    )

    with pytest.raises(ValueError, match="unauthorized verification"):
        validated_result(session, outcome, service.provider("provider-a").terminal_rights)


@pytest.mark.parametrize(
    "failure",
    [
        {"chip_authentication": False},
        {"passive_authentication": False},
        {"blacklist_checked": False},
        {"validity_date_checked": False},
        {"expired": True},
        {"revoked": True},
    ],
)
def test_all_document_validity_checks_are_mandatory(service, failure):
    session = service.use_id("provider-a", UseIDRequest({"GivenNames": AttributeRequest.REQUIRED}))
    outcome = EACOutcome(
        data={"GivenNames": "ERIKA"},
        user_authorized=frozenset({"GivenNames"}),
        on_chip=frozenset({"GivenNames"}),
        evidence=evidence(**failure),
    )
    with pytest.raises(Exception, match="validity"):
        validated_result(session, outcome, service.provider("provider-a").terminal_rights)
