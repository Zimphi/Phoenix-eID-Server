# Phoenix eID Server

Open-source test eID server for integrating the Phoenix ePassport Simulator
with the AusweisApp SDK and virtual eID profiles.

## Scope

The repository is intended to provide:

- a `TcToken` endpoint for AusweisApp SDK `RUN_AUTH` sessions;
- the server side of a test EAC flow;
- a test-only CVCA → DV → terminal certificate chain;
- profile-aware CHAT access rights;
- callback and result endpoints for the simulator gateway;
- integration tests against the AusweisApp SDK card simulator and Phoenix
  virtual eID profiles.

It does **not** contain a production authorization certificate, production
private keys, or credentials for the German eID production infrastructure.

## Trust models

Two test modes are planned:

1. **AusweisApp Test-PKI** — official test profiles and an external test eID
   service.
2. **Phoenix Test-PKI** — Phoenix profiles whose `EF.CVCA` trusts a locally
   generated test CVCA. DV and terminal credentials are generated locally and
   remain outside version control.

The AusweisApp SDK is the client component. This repository implements the
corresponding test service; the SDK itself does not supply reusable terminal
credentials for an arbitrary service.

## Planned package layout

```text
src/phoenix_eid_server/
  tctoken/       TcToken and session endpoints
  eac/           terminal-authentication orchestration
  pki/           test-PKI generation and credential loading
  gateway/       Phoenix simulator integration
tests/           protocol and integration tests
docs/            architecture and operational guidance
```

## Security

This project is for development and interoperability testing only. Never
commit private keys, authorization certificates issued for a real service,
PINs, CANs, API tokens, or production eID data. See `SECURITY.md`.

## License

Licensed under the European Union Public Licence, version 1.2 (`EUPL-1.2`).

