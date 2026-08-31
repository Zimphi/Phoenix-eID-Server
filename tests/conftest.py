import pytest

from phoenix_eid_server.config import ServerConfig, ServiceProvider
from phoenix_eid_server.service import EIDService


@pytest.fixture
def service():
    config = ServerConfig(
        ecard_server_url="https://eid.example.test:9443/ecard",
        providers={
            "provider-a": ServiceProvider(
                identifier="provider-a",
                refresh_url="https://service.example.test/refresh/unguessable",
                communication_error_url="https://service.example.test/error",
                terminal_rights=frozenset(
                    {"GivenNames", "FamilyNames", "AgeVerification", "RestrictedID"}
                ),
                max_sessions=2,
            )
        },
        session_ttl_seconds=300,
        token_ttl_seconds=120,
    )
    return EIDService(config)
