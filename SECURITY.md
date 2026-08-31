# Security policy

## Intended use

Phoenix eID Server is a test and development component. It is not a certified
eID server and must not be connected to the German production eID
infrastructure.

The current repository is a protocol and policy core. It is intentionally not
possible to start the SOAP listener without a WS-Security provider or the
eCard listener without a PAOS/EAC provider. Implementations of those providers
must be assessed against TR-03130-4 and the referenced TR-03110, TR-03112,
TR-03116 and TR-03129 requirements.

## Deployment invariants

- Terminate the three trust boundaries with the dedicated TLS contexts from
  the application; do not merge them at an unaware reverse proxy.
- Keep the SOAP client-certificate fingerprint allow-list current.
- Store terminal and XML-signing private keys in an HSM or equivalent protected
  cryptographic module in production-like tests.
- Never log request targets, PSK identities, SOAP bodies, TcTokens, APDUs, or
  personal data.
- Run all three listeners in one process until an atomic encrypted distributed
  SessionStore is available.
- Treat health endpoints as liveness only; they expose no configuration or
  session data.

## Credentials

Generate test keys locally and store them outside the repository. Do not
submit production authorization certificates, private keys, PINs, CANs,
TcTokens, access tokens, or personal eID data in issues or pull requests.

Public test certificates may be added only when their origin, licence, test
purpose, and absence of corresponding private production material are
documented.

## Reporting

Please report suspected vulnerabilities privately to the repository owner
before publishing technical details.
