# Phoenix eID Server

Python-Kern eines fail-closed Test-eID-Servers für den Phoenix ePassport
Simulator und die AusweisApp. Referenz ist BSI TR-03130-1 v2.4.0; das Projekt
ist weder BSI-zertifiziert noch eine fertige Wirkbetriebs-Komponente.

## Scope

Implementiert sind:

- `useID`, `getResult` und `getServerInfo` als SOAP-1.1-eID-Interface;
- sichere, ablaufende und mandantenbegrenzte Sitzungen mit Einmalergebnis;
- zufällige Session-IDs und TLS-PSKs sowie Replay-Schutz über `RequestCounter`;
- ein normativ geordnetes `TCTokenType` mit einmaligem Token-Handle;
- strikte Rechtefilterung für Requested/Required/Optional CHAT;
- drei getrennte HTTPS-Grenzen für eService-mTLS, öffentliches TcToken und
  RSA-PSK-PAOS;
- fail-closed Provider-Schnittstellen für WS-Security und PAOS/EAC2;
- erzwungene Nachweise für Chip Authentication, Passive Authentication,
  Ablaufdatum und Blacklist, bevor personenbezogene Daten freigegeben werden.

Nicht mitgeliefert sind ein kryptographischer PAOS/EAC2-Provider, eine
WS-Security-Implementierung, TR-03129/BerCA-Anbindung, produktive
Berechtigungszertifikate oder ein Sicherheitskonzept des konkreten Betriebs.
Ohne diese Komponenten startet der jeweilige Netzwerk-Listener nicht.

Der genaue Nachweisstand steht in
[`docs/TR-03130-COMPLIANCE.md`](docs/TR-03130-COMPLIANCE.md).

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

## Paketstruktur

```text
src/phoenix_eid_server/
  service.py          eID-Interface-Anwendungslogik
  sessions.py         TTL, Limits, Replay-Schutz, sichere Löschung
  soap.py             SOAP-Codec für useID/getResult/getServerInfo
  tctoken.py          TR-03124-TcToken
  http.py             getrennte HTTP-Routen und Sicherheitsgrenzen
  tls.py              mTLS und RSA-PSK-TLS-Kontexte
  eac.py              PAOS/EAC-Providervertrag und Ergebnisvalidierung
  message_security.py WS-Security-Providervertrag
tests/                 Protokoll-, Policy- und Negativtests
```

## Entwicklung

```console
python -m pip install -e .
pytest
```

Der vollständige Drei-Listener-Betrieb verwendet denselben Prozess und damit
denselben kurzlebigen Sitzungsspeicher:

```console
phoenix-eid-server \
  --config config.json \
  --backend my_eac_provider:create \
  --message-security my_wssecurity_provider:create
```

`config.example.json` enthält ausschließlich Platzhalter. Der eCard-Listener
benötigt Python 3.13 oder neuer mit OpenSSL-PSK-Unterstützung. `identifier`
eines Providers ist der kleingeschriebene SHA-256-Fingerprint seines
mTLS-Clientzertifikats. Nach `useID` bildet das eService die TcToken-URL als
`https://<public-listener>/tctoken/<Session.ID>`.

## Sicherheit

Keine privaten Schlüssel, PIN/CAN, TcTokens oder echte eID-Daten committen.
Details stehen in `SECURITY.md`.

## License

Licensed under the European Union Public Licence, version 1.2 (`EUPL-1.2`).
