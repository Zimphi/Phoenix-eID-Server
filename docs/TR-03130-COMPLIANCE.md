# BSI TR-03130 Compliance-Matrix

Arbeitsstand gegen TR-03130-1 v2.4.0 und TR-03130-2 v2.1.2. Diese Matrix ist
keine Konformitätserklärung und ersetzt weder TR-03130-4-Tests noch eine
Zertifizierung.

| Anforderung | Stand | Nachweis / Restarbeit |
|---|---|---|
| 2.3.1 eService-Kommunikation | teilweise | mTLS-Listener, Provider-Isolation und PSK-Aushandlung implementiert; WS-Security ist fail-closed Providervertrag |
| 2.3.2 eCard-API | Provider | TLS_RSA_PSK_WITH_AES_256_CBC_SHA sowie das aktuell von TR-03116-4 geforderte TLS_RSA_PSK_WITH_AES_128_CBC_SHA256 und Sessionauflösung implementiert; StartPAOS, DIDAuthenticate EAC1/EAC2/EACAdditional und Transmit müssen vom PAOSBackend implementiert werden |
| 2.3.3 TR-03129 PKI | offen | RequestCertificate, GetMasterList, GetSectorPublicKey, GetBlackList und optional GetDefectList fehlen |
| 2.4 Dokumentvalidierung | Policy erfüllt, Kryptographie Provider | Freigabe verlangt CA, PA, Datum und Blacklist; CMS/CSCA/CRL/Blacklist-Prüfung ist Aufgabe eines noch fehlenden geprüften Providers |
| 3.2.1 useID | Kern implementiert | Operationen, Zusatzargumente, Terminalrechte, PSK, Limits und Fehlercodes |
| 3.2.2 getResult | Kern implementiert | Polling, noResultYet, streng steigender RequestCounter, Einmalabruf und Löschung |
| 3.2.3 getServerInfo | implementiert | Version 2.4.0 und konfigurierte Terminalrechte |
| 3.3 Datentypen | teilweise | nationale Kerntypen umgesetzt; Validierung erfolgt strukturell, die amtliche XSD ist noch nicht eingebunden |
| 3.4 Fehlercodes | implementiert für Kern | common/useID/getResult-Mapping vorhanden; PAOS-Provider muss TR-03112-Fehler ergänzen |
| 3.5.1 Verschlüsselung | implementiert | getrennte TLS-Kontexte; SOAP mTLS ist zwingend |
| 3.5.2 XML-Signatur | Provider | Listener startet ohne MessageSecurity nicht; Basic*Sha256/WS-Security-Policy-Implementierung fehlt im Repository |
| 3.5.3 Session Binding | Kern implementiert | PSK-ID, PSK, Einmal-TcToken und PSK-Auflösung sind an dieselbe Session gebunden |
| TR-03124 TcToken | implementiert | HTTPS-Adressen, Reihenfolge, PAOS-Binding, RFC-4279 und 256-Bit-PSK |
| SAML-Profil Abschnitt 4 | nicht gewählt | SOAP-Profil wird verwendet; SAML ist die alternative eService-Schnittstelle |
| eIDAS-Erweiterung Abschnitt 5 | optional/offen | nicht Teil des nationalen Testserver-Profils |
| TR-03130-2 Sicherheitsrahmen | betriebliche Aufgabe | Die separate [R.1-R.20-Checkliste](TR-03130-2-OPERATIONS.md) erfasst die Betreiberpflichten; Grundschutz-Sicherheitskonzept, Rollen, HSM, Monitoring, physische Sicherheit und Netzwerkzonen sind deploymentspezifisch |
| TR-03130-4 Testbed | offen | Offizielles Testbed wurde zur Strukturprüfung herangezogen; vollständiger Lauf setzt PAOS/EAC-, PKI- und WS-Security-Provider sowie Testkarten voraus |

## Abnahmekriterien für den Status „konformitätsreif“

1. Amtliche WSDL/XSD vollständig einbinden und positive wie negative
   Schemafälle testen.
2. WS-Security mit X.509 Initiator-/RecipientToken, ausschließlich zulässigen
   SHA-256-Suites, Wrapping-Schutz, Zeitfenster und Replay-Cache implementieren.
3. PAOS/EAC2 samt CVC-Kette, CertificateDescription, CHAT, TA, CA, RI/Auxiliary
   Data und Transmit gegen TR-03110/-03112-Testvektoren implementieren.
4. ICAO-CSCA-Truststore, CMS/Passive Authentication, CRLs, Master Lists und
   eID-Blacklist über TR-03129 implementieren.
5. Den vollständigen anwendbaren Testsatz des offiziellen
   `eID-Testbeds/server` reproduzierbar protokollieren.
6. Ein deploymentspezifisches Sicherheitskonzept nach TR-03130-2 erstellen und
   Schlüssel in einer geeigneten geschützten Komponente betreiben.
