# Architektur

```text
eService ── mTLS + WS-Security ── :8443 /eid (SOAP)
                                      │
Browser/AusweisApp ── HTTPS ───── :8444 /tctoken/{handle}
                                      │ gemeinsamer SessionStore
AusweisApp ── TLS_RSA_PSK + PAOS ─ :9443 /ecard
                                      │
                              PAOSBackend / EAC2
                                      │
                         Test-CVCA → DV → Terminal
```

Die Listener liegen absichtlich auf getrennten TLS-Kontexten. Das eService wird
beim SOAP-Listener gegenseitig TLS-authentisiert und zusätzlich auf
Nachrichtenebene geprüft. Der öffentliche Listener gibt TcTokens nur einmalig
und mit `no-store` aus. Der eCard-Listener akzeptiert ausschließlich den von
TR-03130 geforderten RSA-PSK-Cipher und löst die `psk_identity` gegen eine
aktive Session auf.

`PAOSBackend` besitzt die kryptographische EAC2-Zustandsmaschine. Der Kern
akzeptiert ein Ergebnis erst, wenn der Provider Chip Authentication, Passive
Authentication, Gültigkeitsdatum und Blacklist-Prüfung positiv nachweist. Eine
zweite Policy-Grenze schneidet Daten auf Schnittmenge aus Anforderung,
Terminalrecht, Nutzerauswahl und tatsächlich auf dem Chip vorhandenen Daten.

CSCA/Document-Signer-Trust und CVCA/DV/Terminal-Trust bleiben getrennt. Der
Kern speichert PSKs als löschbare `bytearray` und entfernt sie beim finalen
`getResult` oder Ablauf. Für mehrere Prozesse ist vor einer Skalierung ein
verschlüsselter, atomarer gemeinsamer SessionStore zu implementieren; die CLI
startet daher alle drei Listener in einem Prozess.
