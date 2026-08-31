# TR-03130-2 Betriebs-Checkliste

TR-03130-2 v2.1.2 fordert ein allgemeines ISMS nach ISO 27001 bzw.
IT-Grundschutz und ergänzt es um zwanzig eID-spezifische Anforderungen. Diese
Punkte können nicht allein durch das Python-Paket erfüllt werden und sind vor
jedem produktionsnahen Betrieb nachweisbar umzusetzen.

| ID | Pflichtnachweis des Betreibers |
|---|---|
| R.1 | Dokumentiertes Rollenkonzept, Funktionstrennung und Need-to-know; PiC, ITSO, DPO, Administration und Nutzer gemäß Ausschlussmatrix |
| R.2 | Erst- und Wiederholungsschulung, regelmäßige Qualifikationsprüfung und qualifizierte Stellvertretungen |
| R.3 | Dokumentiertes Zulassungs-/Accountkonzept, starke Authentisierung, geschützte Fernadministration und minimale Zulassungen |
| R.4 | Dokumentiertes Zugriffskonzept und Vier-Augen-Prinzip für HSM-Daten und private Schlüssel |
| R.5 | Kryptokonzept für Schlüssel- und Zertifikatslebenszyklus nach aktueller TR-02102 und CP CVCA eID |
| R.6 | Dokumentiertes Gebäude-/Raumzutrittskonzept mit minimalem Personenkreis |
| R.7 | Gesicherte Bereiche, getrennter Brandabschnitt für Backups, Zutrittskontrolle und Gefahrenmeldeanlage |
| R.8 | Technische Kontrolle, Überwachung und Dokumentation von Zutritt und Anwesenheit |
| R.9 | Administratorzugang zu Sicherheitsbereichen; alle anderen Personen nur begleitet |
| R.10 | Change-, Release-, Update- und sichere Außerbetriebnahmeprozesse inklusive Datenvernichtung |
| R.11 | Aktiver Malware-Schutz auf allen Systemen außer HSM und kontrollierte Datenträger |
| R.12 | Zeitnahe stabile Sicherheitsupdates unter Beachtung des Change-Prozesses |
| R.13 | Logging von Logins, Zugriffsversuchen, Administration und Webservice-Zugriffen; Alarm nach mehr als drei Fehlanmeldungen |
| R.14 | Gehärtete Minimalinstallation, Least Privilege, dokumentierte Rechte und Bootschutz |
| R.15 | Mindestens wöchentliche dokumentierte Integritätsprüfung und Abschaltung bei Fehler |
| R.16 | Internet-, DMZ- und interne Zone; physisch getrennter Web- und Application-Server |
| R.17 | Firewallkette aus Paketfilter, ALG und Paketfilter; vollständiges Connection-Logging, tägliche Prüfung und fail-closed bei Logging-Ausfall |
| R.18 | IDS mit signatur-, protokoll- und anomaliebasierter Erkennung sowie zeitnaher Alarmierung |
| R.19 | Vertragliche Verpflichtung ausgelagerter Betreiber auf sämtliche TR-03130-2-Anforderungen |
| R.20 | Nachweis aller anwendbaren gesetzlichen Pflichten und Sicherheitsmaßnahmen aus TR-03130-1 |

Zusätzlich gelten Datenschutzrecht, PAuswG/PAuswV, TR-03128-2 sowie die
Certificate Policy unabhängig von dieser Checkliste. Verfügbarkeit und das
konkrete Backup-/Wiederanlaufziel sind risikobasiert mit dem eService
festzulegen.
