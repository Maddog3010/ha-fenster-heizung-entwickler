# Strom & Wärme – Entwickler-Version

Das ist die **Entwickler-Version** von [Strom & Wärme](https://github.com/Maddog3010/ha-fenster-heizung). Sie ist nur für den Entwickler gedacht und **nicht für den normalen Betrieb**.

- **Gesperrt ab Start.** Ohne gültigen Entwickler-Schlüssel (`FHDEV1-…`) zeigt die Integration nur einen Sperrbildschirm. Es gibt keine Module, keine Steuerung, keine Sensoren oder Schalter und keine Dienste. Die Schnittstelle lehnt alles außer dem Entsperren ab.
- **Eigener Name.** Domain `fenster_heizung_dev`, Seitenleiste „Strom & Wärme Entwickler“. Sie läuft neben der normalen Version, ohne dass sich beide stören.
- **Bereich „Entwicklung“.** Nach dem Entsperren erscheint in der Modulleiste „Entwicklung“ mit dem Knopf **Ins Hauptprojekt veröffentlichen**.

## Installation (HACS)
1. HACS → Benutzerdefinierte Repositories → `https://github.com/Maddog3010/ha-fenster-heizung-entwickler`, Typ „Integration“.
2. „Strom & Wärme Entwickler“ laden, Home Assistant neu starten.
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → „Strom & Wärme Entwickler“ (einen Raum anlegen).
4. In der Seitenleiste „Strom & Wärme Entwickler“ öffnen und den Entwickler-Schlüssel eingeben.

Den Schlüssel erzeugt und signiert nur der Entwickler. Er wird lokal geprüft und im Home-Assistant-Speicher abgelegt. „Sperren“ im Bereich „Entwicklung“ sperrt wieder alles.

## Einmalig einrichten: Veröffentlichen per Knopf
Der Knopf startet einen GitHub-Workflow (`.github/workflows/release.yml`). Der baut die Version **ohne Entwickler-Teile** und legt einen Commit auf `main` im Hauptprojekt an. Einen **Release legst du danach selbst an** (der Knopf „Release auf GitHub anlegen“ öffnet die Seite mit dem Tag).

Dafür zwei Tokens (GitHub → Settings → Developer settings → Fine-grained personal access tokens):

| Token | Repository | Rechte | Wohin |
|---|---|---|---|
| Hauptprojekt schreiben | `ha-fenster-heizung` | Contents: Read and write | Geheimnis `MAIN_REPO_TOKEN` im Entwickler-Repo (Settings → Secrets and variables → Actions) |
| Workflow starten | `ha-fenster-heizung-entwickler` | Actions: Read and write | In der App unter „Entwicklung → Zugang → GitHub-Token“ |

Das Token mit Schreibrecht aufs Hauptprojekt liegt damit nur bei GitHub und nie in Home Assistant.

## Aufbau
- `custom_components/fenster_heizung_dev/` Quelltext der Integration, `devgate.py` und `devapi.py` sind nur hier.
- `frontend-src/parts/` Oberfläche in Teilen, `python3 frontend-src/build.py` baut `panel.js`. `12j-entwicklung.js` ist nur hier.
- `release/` README, CHANGELOG und HACS-Datei des Hauptprojekts.
- `tools/release_build.py` macht daraus die Version für das Hauptprojekt.

Entwickler-Code steht in Blöcken, die beim Veröffentlichen entfernt werden:

```
# <DEV>            (JavaScript: //<DEV>)
nur in der Entwickler-Version
# <RELEASE>
#> Zeile, die im Hauptprojekt gilt (mit #> bzw. //> davor)
# </DEV>
```

Beim Bauen wird geprüft, dass im Ergebnis kein Rest des Entwickler-Modus und kein privater Schlüssel steckt.
