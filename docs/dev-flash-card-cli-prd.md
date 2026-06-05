Executive Summary (TL;DR)

Hier ist die konsolidierte PRD mit den finalen Entscheidungen: **explizite Card-IDs, JSON-Sidecars, `review` braucht `deck + card_id`, Python, headless MVP, Markdown-Dateien als Decks.**

````markdown
# PRD: Headless Markdown Spaced-Repetition CLI for AI-Agent-Based Learning

## 1. Executive Summary

Dieses Produkt ist ein headless, Markdown-basiertes Spaced-Repetition-CLI für terminal- und agentengestützte Lernprozesse.

Der User pflegt Lernkarten in Markdown-Dateien. Jede Markdown-Datei entspricht einem Deck. Karten werden entweder explizit über `#flashcard` an Überschriften markiert oder im Auto-Mode aus Überschriften abgeleitet. Das CLI stellt fällige Karten bereit, nimmt Review-Ratings entgegen und aktualisiert den Lernfortschritt über einen SM-2-basierten Scheduler.

Der primäre Consumer ist nicht ein Mensch in einer TUI, sondern ein KI-Agent. Der Agent ruft über CLI-Kommandos fällige Karten ab, stellt dem User die Fragen im Chat, bewertet die Antwort semantisch und meldet das Review-Ergebnis an das CLI zurück.

Das MVP ist bewusst headless. Es enthält keine TUI, keine Neovim-Integration, keine MCP-Schnittstelle, keine Tags/Filter, keine Rubrics im Datenmodell, keine User-Antwortspeicherung und keine Review-Historie.

---

## 2. Product Vision

### 2.1 Zielbild

Das Tool soll den Lernprozess in eine terminal- und agentenfreundliche Form bringen:

```text
Markdown Decks
    ↓
Headless CLI
    ↓
AI Agent
    ↓
User beantwortet Fragen im Chat
    ↓
AI Agent bewertet Antwort
    ↓
CLI speichert Review-State im Sidecar
````

Der User soll perspektivisch nur noch mit dem KI-Agenten sprechen müssen. Das CLI ist die zuverlässige, deterministische Lern-Engine im Hintergrund.

### 2.2 Kernidee

* Markdown bleibt das authoring-freundliche Format.
* Sidecar-JSON speichert den Review-State Git-freundlich neben dem Deck.
* Das CLI ist non-interactive und scriptbar.
* Der Agent kann über einfache Commands Karten abrufen und Reviews zurückmelden.
* Die semantische Bewertung liegt beim Agenten, nicht beim CLI.
* Das CLI entscheidet nur über Scheduling und Persistenz.

---

## 3. Problem Statement

Bestehende Lösungen sind für diesen Use Case ungeeignet, weil sie typischerweise mindestens eines der folgenden Probleme haben:

* zu stark TUI-/UI-zentriert
* nicht agentenfreundlich
* kein klares headless CLI
* kein Markdown als echte Source of Truth
* kein sauberer Sidecar-State
* unklare oder instabile Schnittstellen für Automation
* Review-Flow erwartet direkte menschliche Interaktion mit dem Tool
* keine gute Trennung zwischen Content, Review-State und semantischer Bewertung

Das gewünschte Tool soll nicht primär eine Flashcard-App sein, sondern eine **headless learning engine** für Markdown-Karten.

---

## 4. Goals

### 4.1 Product Goals

1. Markdown-Dateien als primäre Quelle für Lernkarten nutzen.
2. Eine Datei als ein Deck behandeln.
3. Karten mit stabilen expliziten IDs versehen.
4. Review-State getrennt vom Markdown in JSON-Sidecars speichern.
5. Fällige Karten per CLI abrufbar machen.
6. Reviews per CLI zurückmelden können.
7. Agentenfreundliche, stabile Kommandos anbieten.
8. SM-2-Scheduling im MVP implementieren.
9. Architektur so schneiden, dass FSRS später ergänzt werden kann.
10. Python als Implementierungssprache verwenden.

### 4.2 User Goals

Der User möchte:

* Lernkarten in Markdown pflegen.
* Karten durch einen KI-Agenten erstellen, pflegen und prüfen lassen.
* Im Terminal-First-Workflow bleiben.
* Nicht in einer TUI oder App lernen müssen.
* Fällige Karten durch einen Agenten gestellt bekommen.
* Antworten frei formulieren können.
* Die semantische Bewertung durch den Agenten durchführen lassen.
* Den Lernfortschritt versionierbar im Git-Repo halten.
* Später optional eine TUI auf Basis desselben Cores nutzen können.

### 4.3 Agent Goals

Der AI-Agent soll:

* fällige Karten per CLI abrufen können.
* optional direkt Musterantworten erhalten können.
* dem User nur die Frage stellen.
* die User-Antwort gegen die Musterantwort bewerten.
* ein Rating ableiten: `again`, `hard`, `good`, `easy`.
* das Rating per CLI zurückmelden.
* optional mehrere Karten auf einmal abrufen können.
* keine interaktive TUI bedienen müssen.

---

## 5. Non-Goals

### 5.1 Nicht Teil des MVP

* Keine TUI.
* Keine Neovim-Integration.
* Kein MCP-Server.
* Keine HTTP API.
* Keine Tags oder Filter.
* Keine Rubrics als strukturiertes Datenmodell.
* Keine Cloze Cards.
* Keine reversed Cards.
* Kein Anki-Import/-Export.
* Kein FSRS im MVP.
* Keine User-Antwortspeicherung.
* Keine Review-Historie.
* Kein Multi-User-Modus.
* Kein Sync-Service.
* Keine Cloud-Komponente.
* Keine eingebaute LLM-/AI-Integration.
* Keine automatische semantische Bewertung im CLI.
* Keine komplexe Wissensbasis-/PKM-Integration.
* Keine automatische Extraktion von Karten aus unstrukturierten Notizen im MVP.

### 5.2 Spätere mögliche Erweiterungen

* Textual-basierte TUI.
* MCP-Server.
* FSRS-Scheduler.
* Tags und Filter.
* Rubric-Unterstützung.
* Review-Historie.
* Optionales Speichern von User-Antworten.
* Import/Export.
* Anki-Export.
* Auto-Generation von Karten durch externe Agenten.
* Validierung von Kartenqualität.
* Deck-Statistiken über mehrere Repos.
* Weakness-Analyse.
* Multi-Deck-Sessions.
* Lernzeit-basierte Sessions.

---

## 6. Target Users

### 6.1 Primary User

Terminal-affiner Entwickler/Architekt, der:

* Markdown bevorzugt
* Git zur Versionierung nutzt
* CLI-first arbeitet
* KI-Agenten als Interface nutzen möchte
* Lerninhalte strukturiert, aber mit geringer Pflegekosten halten will

### 6.2 Secondary User

Power-User mit:

* Markdown-Notizen
* Spaced-Repetition-Bedarf
* Interesse an scriptbaren Lernsystemen
* Wunsch nach späterer TUI, aber sauberem headless Core

### 6.3 Primary Consumer

Der primäre technische Consumer ist ein AI-Agent, nicht der direkte Mensch.

---

## 7. Core Workflow

### 7.1 Authoring Workflow

```bash
recall deck create architecture
```

Erzeugt:

```text
decks/
  architecture.md
  architecture.flashcards.json
```

Der User oder ein Agent ergänzt Karten:

```markdown
# Architecture

## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS trennt das Command-/Write-Modell vom Query-/Read-Modell.
```

### 7.2 Learning Workflow über AI-Agent

1. Agent ruft fällige Karten ab:

```bash
recall next --deck architecture --limit 5 --show-answer
```

2. CLI gibt Karten aus.
3. Agent stellt dem User nur die Fragen.
4. User beantwortet die Fragen frei im Chat.
5. Agent bewertet semantisch.
6. Agent meldet Ratings zurück:

```bash
recall review --deck architecture --card-id architecture-cqrs --rating good
```

7. CLI aktualisiert Sidecar-State.

---

## 8. Functional Requirements

## 8.1 CLI Basics

### FR-001: CLI Entrypoint

Das Tool stellt ein CLI mit dem Namen `recall` bereit.

Beispiele:

```bash
recall --help
recall init
recall deck create architecture
recall scan
recall next --deck architecture
recall review --deck architecture --card-id architecture-cqrs --rating good
recall stats
recall validate
```

### FR-002: Headless First

Alle MVP-Kommandos müssen non-interactive ausführbar sein.

Nicht erlaubt im MVP:

* Prompts, die User-Eingabe erzwingen
* TUI
* Cursor-basierte UI
* interaktive Picker
* Vollbildmodus
* Neovim-Abhängigkeit

### FR-003: Deterministische Exit Codes

Das CLI muss stabile Exit Codes liefern:

| Exit Code | Bedeutung                |
| --------: | ------------------------ |
|         0 | Erfolg                   |
|         1 | generischer Fehler       |
|         2 | ungültige CLI-Argumente  |
|         3 | ungültige Konfiguration  |
|         4 | Deck nicht gefunden      |
|         5 | Karte nicht gefunden     |
|         6 | ungültiges Kartenformat  |
|         7 | ungültiger Sidecar-State |
|         8 | keine fälligen Karten    |
|         9 | Schreibfehler            |

### FR-004: Human-readable Default Output

Standardmäßig darf das CLI menschenlesbaren Output liefern.

Beispiel:

```text
Deck: architecture
Due cards: 3

[architecture-cqrs]
Was ist CQRS?
```

### FR-005: Optional JSON Output

Alle agentenrelevanten Commands sollen optional JSON ausgeben können.

Flag:

```bash
--format json
```

Beispiel:

```bash
recall next --deck architecture --limit 5 --show-answer --format json
```

Rationale:

* Agents können Plain stdout lesen.
* JSON reduziert aber fragile Textanalyse.
* JSON erleichtert spätere MCP-/TUI-Integration.
* JSON macht Tests einfacher.

---

## 8.2 Repository / Project Initialization

### FR-010: Init Command

```bash
recall init
```

Initialisiert die lokale Struktur.

Default-Struktur:

```text
.
├── decks/
└── recall.config.json
```

Optional kann das Tool auch in einem bestehenden Verzeichnis arbeiten.

### FR-011: Config File

Das Tool verwendet optional eine Konfigurationsdatei:

```json
{
  "version": 1,
  "decks_dir": "decks",
  "default_auto_mode": false,
  "default_min_heading_level": 2,
  "sidecar_suffix": ".flashcards.json",
  "scheduler": "sm2"
}
```

### FR-012: Keine globale Pflichtkonfiguration

Das Tool soll auch ohne Config funktionieren, wenn explizite Pfade oder Decks angegeben werden.

---

## 8.3 Deck Management

### FR-020: Eine Markdown-Datei = ein Deck

Jede Markdown-Datei repräsentiert genau ein Deck.

Beispiel:

```text
decks/architecture.md
```

entspricht Deck:

```text
architecture
```

### FR-021: Sidecar pro Deck

Zu jedem Deck existiert ein Sidecar:

```text
decks/architecture.flashcards.json
```

### FR-022: Deck Create

```bash
recall deck create architecture
```

Erzeugt:

```text
decks/architecture.md
decks/architecture.flashcards.json
```

Initialer Markdown-Inhalt:

```markdown
# Architecture
```

Initialer Sidecar-Inhalt:

```json
{
  "version": 1,
  "deck": "architecture",
  "cards": {}
}
```

### FR-023: Deck List

```bash
recall deck list
```

Gibt alle gefundenen Decks aus.

Optional:

```bash
recall deck list --format json
```

Beispiel JSON:

```json
{
  "decks": [
    {
      "name": "architecture",
      "path": "decks/architecture.md",
      "sidecar": "decks/architecture.flashcards.json"
    }
  ]
}
```

### FR-024: Deck Naming

Deck-Namen müssen filesystem-kompatibel sein.

Erlaubt:

```text
[a-zA-Z0-9._-]+
```

Nicht erlaubt:

* Slash
* Backslash
* Null bytes
* reine Whitespace-Namen
* leere Namen

---

## 8.4 Markdown Card Format

### FR-030: Heading-based Cards

Eine Karte wird als Markdown-Heading plus Body modelliert.

```markdown
## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS trennt das Command-/Write-Modell vom Query-/Read-Modell.
```

Die Heading-Zeile ist die Frage.

Der Antworttext ist der Markdown-Content nach der Heading-Zeile bis zur nächsten Heading gleicher oder höherer Ebene.

### FR-031: Explizite Card-ID

Jede Karte braucht eine explizite stabile ID.

Format:

```markdown
<!-- recall:id=architecture-cqrs -->
```

Die ID gehört direkt unter die Frage-Heading.

### FR-032: Card-ID Syntax

Erlaubt:

```text
[a-zA-Z0-9._:-]+
```

Empfohlener Stil:

```text
<deck>-<topic>-<slug>
```

Beispiele:

```text
architecture-cqrs
dotnet-async-await
chess-rook-endgame-lucena
```

### FR-033: IDs sind stabil

Eine Karte behält ihren State, solange ihre ID gleich bleibt.

Erlaubte Änderungen ohne State-Verlust:

* Frage umformulieren
* Antwort erweitern
* Antwort korrigieren
* Karte innerhalb der Datei verschieben
* Markdown-Formatierung ändern

Nicht erlaubt:

* gleiche Card-ID mehrfach im selben Deck
* gleiche Card-ID mehrfach in mehreren Decks, wenn globale Eindeutigkeit später benötigt wird

Für das MVP gilt:

```text
card_id muss innerhalb eines Decks eindeutig sein.
review benötigt deck + card_id.
```

### FR-034: Tagged Mode

Im Tagged Mode werden nur Headings mit `#flashcard` als Karten erkannt.

Beispiel:

```markdown
## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

Antwort...
```

### FR-035: Auto Mode

Im Auto Mode werden alle Headings ab `min_heading_level` als Karten behandelt.

Beispiel-Konfiguration:

```json
{
  "default_auto_mode": true,
  "default_min_heading_level": 2
}
```

Im Auto Mode ist `#flashcard` nicht erforderlich.

Trotz Auto Mode bleibt die explizite Card-ID erforderlich.

### FR-036: Empty Answers

Karten ohne Antworttext sind ungültig.

`validate` muss sie melden.

### FR-037: YAML Frontmatter

YAML Frontmatter am Anfang einer Markdown-Datei darf nicht als Karteninhalt interpretiert werden.

Beispiel:

```markdown
---
title: Architecture
---

# Architecture
```

### FR-038: Fenced Code Blocks

Headings innerhalb fenced code blocks dürfen nicht als Karten erkannt werden.

Beispiel:

````markdown
```markdown
## Not a card #flashcard
```
````

### FR-039: Subheadings im Antwortbereich

Default:

```text
include_sub_headings = true
```

Das bedeutet:

```markdown
## Frage? #flashcard
<!-- recall:id=example -->

Antwort.

### Details

Weitere Antwortdetails.
```

`### Details` ist Teil der Antwort und keine eigene Karte.

Spätere Option:

```json
{
  "include_sub_headings": false
}
```

Dann beendet jedes nächste Heading die Antwort.

Für MVP reicht der Default `include_sub_headings = true`.

---

## 8.5 Markdown Mutation / Maintenance

### FR-040: CLI darf Markdown pflegen

Das CLI darf Markdown-Dateien anlegen und pflegen.

Das umfasst:

* Deck-Dateien anlegen
* leere Decks initialisieren
* Card-ID-Blöcke ergänzen, wenn per explizitem Kommando gewünscht
* Formatvalidierung durchführen
* optional Normalisierung durchführen

### FR-041: Keine Review-Metadaten im Markdown

Das CLI darf keine Scheduling-Daten in Markdown schreiben.

Nicht erlaubt:

```markdown
due: 2026-06-10
ease: 2.5
interval: 6
```

Scheduling-State gehört ausschließlich ins Sidecar.

### FR-042: Normalize Command

```bash
recall normalize --deck architecture
```

Mögliche Aufgaben:

* fehlende Card-IDs ergänzen
* ungültige ID-Positionen korrigieren
* `#flashcard` normalisieren
* Whitespace um ID-Kommentare bereinigen

Für MVP kann `normalize` einfach bleiben.

MVP-Minimum:

* fehlende IDs erkennen
* mit `--write` IDs schreiben
* ohne `--write` nur Vorschau/Fehler anzeigen

Beispiel:

```bash
recall normalize --deck architecture --write
```

### FR-043: ID-Erzeugung durch CLI

Wenn das CLI IDs erzeugt, sollen sie deterministisch lesbar sein.

Beispiel:

Frage:

```text
Was ist CQRS?
```

Deck:

```text
architecture
```

Vorschlag:

```text
architecture-was-ist-cqrs
```

Bei Kollision:

```text
architecture-was-ist-cqrs-2
```

---

## 8.6 Scanning

### FR-050: Scan Command

```bash
recall scan
```

Scannt alle Deck-Dateien.

Output:

```text
Scanned 3 decks, 42 cards, 5 due.
```

JSON:

```json
{
  "decks_scanned": 3,
  "cards_total": 42,
  "cards_due": 5,
  "errors": []
}
```

### FR-051: Scan einzelnes Deck

```bash
recall scan --deck architecture
```

### FR-052: Scan validiert Struktur grob

Scan soll mindestens erkennen:

* Deck-Datei existiert
* Sidecar existiert oder kann erzeugt werden
* Karten sind parsebar
* Card-IDs sind eindeutig
* notwendige Felder vorhanden

### FR-053: Sidecar Auto-Creation

Wenn für ein existierendes Deck kein Sidecar existiert, darf `scan` ein Sidecar erzeugen.

Beispiel:

```json
{
  "version": 1,
  "deck": "architecture",
  "cards": {}
}
```

---

## 8.7 Next Cards

### FR-060: Next Command

```bash
recall next --deck architecture
```

Gibt die nächste fällige Karte aus.

Default:

```text
[architecture-cqrs]
Was ist CQRS?
```

### FR-061: Limit

```bash
recall next --deck architecture --limit 5
```

Gibt bis zu 5 fällige Karten aus.

Das ist MVP-Batch auf Retrieval-Seite.

### FR-062: Keine vollständige Batch-Session im MVP

Das MVP unterstützt:

```bash
recall next --deck architecture --limit 5
```

Aber keine komplexe Session-Verwaltung.

Review erfolgt pro Karte:

```bash
recall review --deck architecture --card-id architecture-cqrs --rating good
```

### FR-063: Optional Answer Output

Standardmäßig gibt `next` nur die Frage aus.

Mit `--show-answer` gibt `next` zusätzlich die Antwort aus.

```bash
recall next --deck architecture --limit 5 --show-answer
```

Rationale:

* Ohne `--show-answer` ist es als direktes Lern-CLI nutzbar.
* Mit `--show-answer` ist es für den AI-Agenten nützlich.
* Der Agent darf die Antwort sehen, soll dem User aber zunächst nur die Frage stellen.

### FR-064: JSON Output für Next

```bash
recall next --deck architecture --limit 2 --show-answer --format json
```

Beispiel:

```json
{
  "deck": "architecture",
  "cards": [
    {
      "card_id": "architecture-cqrs",
      "question": "Was ist CQRS?",
      "answer": "CQRS trennt das Command-/Write-Modell vom Query-/Read-Modell.",
      "source": {
        "path": "decks/architecture.md",
        "line": 3
      },
      "state": {
        "due": "2026-06-05",
        "interval": 0,
        "ease": 2.5,
        "reps": 0
      }
    }
  ]
}
```

Wenn `--show-answer` nicht gesetzt ist:

```json
{
  "deck": "architecture",
  "cards": [
    {
      "card_id": "architecture-cqrs",
      "question": "Was ist CQRS?",
      "source": {
        "path": "decks/architecture.md",
        "line": 3
      },
      "state": {
        "due": "2026-06-05",
        "interval": 0,
        "ease": 2.5,
        "reps": 0
      }
    }
  ]
}
```

### FR-065: Reihenfolge fälliger Karten

MVP-Verhalten:

* fällige Karten zuerst
* neue Karten gelten als fällig
* stabile Reihenfolge nach Datei-Reihenfolge oder konfigurierbar randomisiert

Empfehlung für MVP:

```text
Default: file order
Optional: --shuffle
```

---

## 8.8 Review

### FR-070: Review Command

Review muss `deck` und `card_id` erhalten.

```bash
recall review --deck architecture --card-id architecture-cqrs --rating good
```

### FR-071: Ratings

Erlaubte Ratings:

```text
again
hard
good
easy
```

Bedeutung:

| Rating | Semantik                      | SM-2 Quality |
| ------ | ----------------------------- | -----------: |
| again  | nicht erinnert / falsch       |            0 |
| hard   | schwer / teilweise / unsicher |            2 |
| good   | korrekt mit Aufwand           |            3 |
| easy   | sicher und vollständig        |            5 |

### FR-072: Review speichert neuen State

Nach einem Review aktualisiert das CLI den State im Sidecar.

Beispiel vorher:

```json
{
  "ease": 2.5,
  "interval": 0,
  "reps": 0,
  "due": "2026-06-05"
}
```

Nach `good`:

```json
{
  "ease": 2.36,
  "interval": 1,
  "reps": 1,
  "due": "2026-06-06"
}
```

Konkrete Werte hängen von der Scheduler-Implementierung ab.

### FR-073: Review darf keine User-Antwort speichern

Das MVP speichert nicht:

* User-Antwort
* Agent-Feedback
* semantische Bewertungserklärung
* Review-Historie

Es wird nur der aktuelle Scheduling-State gespeichert.

### FR-074: Review JSON Output

```bash
recall review --deck architecture --card-id architecture-cqrs --rating good --format json
```

Beispiel:

```json
{
  "deck": "architecture",
  "card_id": "architecture-cqrs",
  "rating": "good",
  "old_state": {
    "ease": 2.5,
    "interval": 0,
    "reps": 0,
    "due": "2026-06-05"
  },
  "new_state": {
    "ease": 2.36,
    "interval": 1,
    "reps": 1,
    "due": "2026-06-06"
  }
}
```

### FR-075: Deck + Card-ID Lookup

`review` sucht die Karte ausschließlich innerhalb des angegebenen Decks.

Nicht erlaubt im MVP:

```bash
recall review --card-id architecture-cqrs --rating good
```

Begründung:

* Sidecar ist deckbezogen.
* Lookup bleibt simpel.
* IDs müssen nur pro Deck eindeutig sein.
* Keine globale Card-Registry nötig.

---

## 8.9 Stats

### FR-080: Stats Command

```bash
recall stats
```

Gibt globale Statistik aus.

Beispiel:

```text
Decks: 3
Cards total: 42
Due today: 5
New: 12
Young: 24
Mature: 6
```

### FR-081: Deck Stats

```bash
recall stats --deck architecture
```

Beispiel:

```text
Deck: architecture
Cards total: 12
Due today: 3
New: 4
Young: 7
Mature: 1
```

### FR-082: JSON Stats

```bash
recall stats --deck architecture --format json
```

Beispiel:

```json
{
  "deck": "architecture",
  "cards_total": 12,
  "due_today": 3,
  "new": 4,
  "young": 7,
  "mature": 1
}
```

---

## 8.10 Validate

### FR-090: Validate Command

```bash
recall validate
```

Prüft alle Decks.

### FR-091: Validate einzelnes Deck

```bash
recall validate --deck architecture
```

### FR-092: Validierungsregeln

`validate` prüft:

* Markdown-Datei existiert.
* Sidecar-JSON ist gültig.
* Deck-Name im Sidecar passt.
* Jede Karte hat eine explizite ID.
* Jede Card-ID ist im Deck eindeutig.
* Jede Karte hat eine Frage.
* Jede Karte hat eine nicht-leere Antwort.
* Jede Sidecar-Card referenziert eine existierende Karte oder wird als orphaned markiert.
* Keine ungültigen Ratings im State.
* Keine ungültigen Due-Dates.
* Keine ungültigen Intervals.
* Keine ungültigen Ease-Werte.

### FR-093: Orphaned Sidecar State

Wenn eine Card-ID im Sidecar existiert, aber nicht mehr im Markdown, wird sie als orphaned gemeldet.

MVP-Verhalten:

* nicht automatisch löschen
* nur melden

Beispiel:

```text
Warning: sidecar contains orphaned card state: architecture-old-card
```

Später möglich:

```bash
recall sidecar prune --deck architecture
```

Nicht MVP.

---

## 9. Sidecar JSON Specification

## 9.1 File Naming

Deck:

```text
decks/architecture.md
```

Sidecar:

```text
decks/architecture.flashcards.json
```

## 9.2 Sidecar Schema v1

```json
{
  "version": 1,
  "deck": "architecture",
  "cards": {
    "architecture-cqrs": {
      "ease": 2.5,
      "interval": 0,
      "reps": 0,
      "due": "2026-06-05"
    }
  }
}
```

## 9.3 Field Definitions

| Field      | Type    | Required | Beschreibung                          |
| ---------- | ------- | -------: | ------------------------------------- |
| `version`  | integer |      yes | Sidecar-Schema-Version                |
| `deck`     | string  |      yes | Deck-Name                             |
| `cards`    | object  |      yes | Map von `card_id` zu Scheduling-State |
| `ease`     | number  |      yes | SM-2 Ease Factor                      |
| `interval` | integer |      yes | aktuelles Intervall in Tagen          |
| `reps`     | integer |      yes | erfolgreiche Wiederholungen           |
| `due`      | string  |      yes | ISO-Date im Format `YYYY-MM-DD`       |

## 9.4 Nicht im MVP-Sidecar

Nicht speichern:

```json
{
  "user_answer": "...",
  "agent_feedback": "...",
  "review_history": [],
  "tags": [],
  "rubric": {},
  "source_hash": "...",
  "question_preview": "..."
}
```

Optional später möglich, aber nicht MVP.

## 9.5 Atomic Writes

Sidecar-Schreibvorgänge müssen atomar sein.

Strategie:

1. neue Datei als `.tmp` schreiben
2. flush/sync, soweit praktikabel
3. atomar auf Zielpfad umbenennen

Beispiel:

```text
architecture.flashcards.json.tmp
→ architecture.flashcards.json
```

## 9.6 Git-Freundlichkeit

Sidecar JSON sollte stabil und diffbar sein:

* pretty-printed
* sortierte Keys
* newline am Dateiende
* keine unnötigen Timestamps
* keine flüchtigen Session-Daten

Empfohlene JSON-Formatierung:

```json
{
  "version": 1,
  "deck": "architecture",
  "cards": {
    "architecture-cqrs": {
      "due": "2026-06-06",
      "ease": 2.36,
      "interval": 1,
      "reps": 1
    }
  }
}
```

---

## 10. Scheduler Specification

## 10.1 MVP Scheduler

MVP verwendet SM-2.

## 10.2 Scheduler Interface

Die Implementierung soll intern ein Scheduler-Interface verwenden, damit FSRS später ergänzt werden kann.

Konzeptionelles Interface:

```python
class Scheduler:
    def new_card(self, today: date) -> CardState:
        ...

    def is_due(self, state: CardState, today: date) -> bool:
        ...

    def review(self, state: CardState, rating: Rating, today: date) -> CardState:
        ...
```

## 10.3 SM-2 New Card

Neue Karten erhalten:

```json
{
  "ease": 2.5,
  "interval": 0,
  "reps": 0,
  "due": "today"
}
```

## 10.4 SM-2 Rating Mapping

| Rating  | Quality |
| ------- | ------: |
| `again` |       0 |
| `hard`  |       2 |
| `good`  |       3 |
| `easy`  |       5 |

## 10.5 SM-2 Scheduling Logic

Pseudo-Code:

```python
if quality < 3:
    interval = 1
    reps = 0
else:
    if reps == 0:
        interval = 1
    elif reps == 1:
        interval = 6
    else:
        interval = ceil(interval * ease)
    reps += 1

ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
ease = max(1.3, ease)
due = today + interval days
```

## 10.6 Timezone / Date Handling

MVP arbeitet mit lokalen Kalendertagen.

Due-Dates sind ISO-Strings:

```text
YYYY-MM-DD
```

Keine Uhrzeiten im MVP.

---

## 11. CLI Command Specification

## 11.1 `recall init`

Initialisiert Projektstruktur.

```bash
recall init
```

Optionen:

```bash
recall init --decks-dir decks
```

Erzeugt:

```text
recall.config.json
decks/
```

## 11.2 `recall deck create`

```bash
recall deck create architecture
```

Erzeugt:

```text
decks/architecture.md
decks/architecture.flashcards.json
```

Fehlerfälle:

* Deck existiert bereits
* ungültiger Deck-Name
* `decks_dir` nicht beschreibbar

## 11.3 `recall deck list`

```bash
recall deck list
recall deck list --format json
```

## 11.4 `recall scan`

```bash
recall scan
recall scan --deck architecture
recall scan --format json
```

## 11.5 `recall validate`

```bash
recall validate
recall validate --deck architecture
recall validate --format json
```

## 11.6 `recall normalize`

```bash
recall normalize --deck architecture
recall normalize --deck architecture --write
```

MVP-Fokus:

* fehlende IDs melden
* mit `--write` fehlende IDs ergänzen

## 11.7 `recall next`

```bash
recall next --deck architecture
recall next --deck architecture --limit 5
recall next --deck architecture --limit 5 --show-answer
recall next --deck architecture --limit 5 --show-answer --format json
```

Pflichtargumente:

* `--deck`

Optionen:

| Option          | Beschreibung           |
| --------------- | ---------------------- |
| `--limit N`     | maximale Anzahl Karten |
| `--show-answer` | Antwort mit ausgeben   |
| `--format json` | JSON-Ausgabe           |
| `--shuffle`     | fällige Karten mischen |

## 11.8 `recall review`

```bash
recall review --deck architecture --card-id architecture-cqrs --rating good
```

Pflichtargumente:

* `--deck`
* `--card-id`
* `--rating`

Optionen:

```bash
--format json
```

## 11.9 `recall stats`

```bash
recall stats
recall stats --deck architecture
recall stats --format json
```

---

## 12. Agent Contract

## 12.1 Agent Responsibility

Der Agent ist verantwortlich für:

* Auswahl des Decks
* Abruf fälliger Karten
* Fragenstellung an den User
* semantische Bewertung der User-Antwort
* Ableitung eines Ratings
* Rückmeldung des Ratings an das CLI

## 12.2 CLI Responsibility

Das CLI ist verantwortlich für:

* Parsen von Markdown-Karten
* Validierung der Struktur
* Bereitstellen fälliger Karten
* Persistieren des Review-States
* Scheduling
* Stats

## 12.3 Bewertung durch Agent

Der Agent soll Ratings wie folgt ableiten:

| User-Antwort                       | Rating  |
| ---------------------------------- | ------- |
| falsch / nicht gewusst             | `again` |
| teilweise korrekt, aber lückenhaft | `hard`  |
| fachlich korrekt, aber unsicher    | `good`  |
| vollständig und sicher             | `easy`  |

## 12.4 Musterantwort

Wenn der Agent bewerten soll, soll er `next` mit `--show-answer` verwenden.

```bash
recall next --deck architecture --limit 5 --show-answer
```

Der Agent darf die Antwort verwenden, soll sie aber dem User nicht vorab zeigen.

## 12.5 Kein Rubric-Datenmodell im MVP

Das CLI kennt keine strukturierten Rubrics.

Empfehlung als Best Practice in der README:

```markdown
## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS trennt das Command-/Write-Modell vom Query-/Read-Modell.

Optional für Agentenbewertung:
- Muss Read/Write-Trennung nennen.
- Sollte Eventual Consistency erwähnen.
```

Das CLI behandelt den gesamten Body als Antworttext.

---

## 13. Markdown Examples

## 13.1 Tagged Mode

```markdown
# Architecture

## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS trennt das Command-/Write-Modell vom Query-/Read-Modell.

## Was ist Eventual Consistency? #flashcard
<!-- recall:id=architecture-eventual-consistency -->

Eventual Consistency bedeutet, dass ein verteiltes System nicht sofort, aber nach einer gewissen Zeit ohne weitere Writes konsistent wird.
```

## 13.2 Auto Mode

Konfiguration:

```json
{
  "default_auto_mode": true,
  "default_min_heading_level": 2
}
```

Markdown:

```markdown
# Architecture

## Was ist CQRS?
<!-- recall:id=architecture-cqrs -->

CQRS trennt das Command-/Write-Modell vom Query-/Read-Modell.

## Was ist Eventual Consistency?
<!-- recall:id=architecture-eventual-consistency -->

Eventual Consistency bedeutet, dass ein verteiltes System nicht sofort, aber nach einer gewissen Zeit ohne weitere Writes konsistent wird.
```

## 13.3 Subheadings als Antwortbestandteil

```markdown
## Was ist ein ADR? #flashcard
<!-- recall:id=architecture-adr -->

Ein ADR dokumentiert eine relevante Architekturentscheidung.

### Typische Struktur

- Context
- Decision
- Consequences
```

Die gesamte Antwort inklusive `### Typische Struktur` gehört zur Karte.

---

## 14. Data Model

## 14.1 Parsed Card

```python
@dataclass
class ParsedCard:
    deck: str
    card_id: str
    question: str
    answer: str
    source_path: str
    line_number: int
    heading_level: int
```

## 14.2 Card State

```python
@dataclass
class CardState:
    ease: float
    interval: int
    reps: int
    due: date
```

## 14.3 Deck

```python
@dataclass
class Deck:
    name: str
    markdown_path: Path
    sidecar_path: Path
    cards: list[ParsedCard]
```

## 14.4 Rating

```python
Rating = Literal["again", "hard", "good", "easy"]
```

---

## 15. Architecture

## 15.1 Components

```text
recall/
  cli.py
  config.py
  decks.py
  markdown_parser.py
  sidecar.py
  scheduler/
    base.py
    sm2.py
  commands/
    init.py
    deck.py
    scan.py
    validate.py
    normalize.py
    next.py
    review.py
    stats.py
```

## 15.2 Dependency Direction

```text
CLI Commands
    ↓
Application Services
    ↓
Parser / Scheduler / Sidecar
    ↓
Filesystem
```

## 15.3 Core Design Rules

* Parser hat keine Sidecar-Logik.
* Scheduler hat keine Markdown-Logik.
* Sidecar kennt keine Markdown-Parsing-Details.
* CLI orchestriert nur.
* Businesslogik ist testbar ohne Shell-Aufrufe.
* Textual-TUI soll später denselben Core verwenden können.

---

## 16. Packaging

## 16.1 Python

Implementierung in Python.

Empfohlene Mindestversion:

```text
Python >= 3.11
```

## 16.2 CLI Framework

Empfehlung:

```text
Typer
```

Alternative:

```text
Click
```

Für MVP ist Typer sinnvoll wegen:

* schneller CLI-Entwicklung
* guter Help-Ausgabe
* Type-Hints
* einfache Testbarkeit

## 16.3 Projektverwaltung

Empfehlung:

```text
uv
```

Beispiel:

```bash
uv init recall
uv add typer rich
```

`rich` optional für menschenlesbare Ausgabe. JSON-Ausgabe darf kein Rich-Markup enthalten.

## 16.4 Installation

MVP lokal:

```bash
uv tool install .
```

Oder während Entwicklung:

```bash
uv run recall --help
```

---

## 17. Testing Requirements

## 17.1 Unit Tests

Pflichtbereiche:

* Markdown parser
* ID extraction
* duplicate ID detection
* Sidecar load/save
* Sidecar atomic write
* SM-2 scheduler
* due detection
* review update
* validate
* normalize dry-run
* normalize write
* JSON output

## 17.2 Golden File Tests

Empfohlen für Markdown Parsing.

Beispiel:

```text
tests/fixtures/architecture.md
tests/fixtures/architecture.expected.json
```

## 17.3 CLI Tests

CLI Tests sollen echte Commands ausführen.

Beispiele:

```bash
recall deck create architecture
recall next --deck architecture --format json
recall review --deck architecture --card-id architecture-cqrs --rating good --format json
```

## 17.4 No Interactive Tests in MVP

Da das MVP headless ist, dürfen Tests keine interaktive UI benötigen.

---

## 18. Acceptance Criteria

## 18.1 MVP Acceptance

Das MVP gilt als fertig, wenn:

* `recall init` Projektstruktur erzeugt.
* `recall deck create <name>` Markdown + Sidecar erzeugt.
* Markdown-Karten mit `#flashcard` korrekt erkannt werden.
* Auto Mode funktioniert.
* explizite Card-IDs erkannt werden.
* fehlende IDs validiert werden.
* doppelte IDs validiert werden.
* Sidecar JSON erzeugt und gepflegt wird.
* `recall next --deck <deck>` fällige Karten liefert.
* `recall next --deck <deck> --limit N` mehrere Karten liefert.
* `recall next --deck <deck> --show-answer` Antworten mit ausgibt.
* `recall review --deck <deck> --card-id <id> --rating <rating>` State aktualisiert.
* SM-2 Scheduling korrekt funktioniert.
* `recall stats` sinnvolle Zahlen liefert.
* `recall validate` Fehler erkennt.
* `recall normalize --deck <deck> --write` fehlende IDs ergänzen kann.
* alle agentenrelevanten Commands `--format json` unterstützen.
* kein Command im MVP interaktive Eingabe benötigt.

---

## 19. Example End-to-End Scenario

### 19.1 Init

```bash
recall init
```

Erzeugt:

```text
recall.config.json
decks/
```

### 19.2 Deck erstellen

```bash
recall deck create architecture
```

Erzeugt:

```text
decks/architecture.md
decks/architecture.flashcards.json
```

### 19.3 Karte ergänzen

```markdown
# Architecture

## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS trennt das Command-/Write-Modell vom Query-/Read-Modell.
```

### 19.4 Validieren

```bash
recall validate --deck architecture
```

Output:

```text
Deck architecture valid.
Cards: 1
Errors: 0
Warnings: 0
```

### 19.5 Nächste Karte holen

```bash
recall next --deck architecture --show-answer --format json
```

Output:

```json
{
  "deck": "architecture",
  "cards": [
    {
      "card_id": "architecture-cqrs",
      "question": "Was ist CQRS?",
      "answer": "CQRS trennt das Command-/Write-Modell vom Query-/Read-Modell.",
      "source": {
        "path": "decks/architecture.md",
        "line": 3
      },
      "state": {
        "due": "2026-06-05",
        "ease": 2.5,
        "interval": 0,
        "reps": 0
      }
    }
  ]
}
```

### 19.6 Agent stellt Frage

Agent fragt User:

```text
Was ist CQRS?
```

### 19.7 User antwortet

```text
Das ist die Trennung von Commands und Queries, also Schreiben und Lesen.
```

### 19.8 Agent bewertet

Agent entscheidet:

```text
rating = good
```

### 19.9 Review speichern

```bash
recall review --deck architecture --card-id architecture-cqrs --rating good --format json
```

Output:

```json
{
  "deck": "architecture",
  "card_id": "architecture-cqrs",
  "rating": "good",
  "old_state": {
    "due": "2026-06-05",
    "ease": 2.5,
    "interval": 0,
    "reps": 0
  },
  "new_state": {
    "due": "2026-06-06",
    "ease": 2.36,
    "interval": 1,
    "reps": 1
  }
}
```

---

## 20. Risks and Trade-offs

## 20.1 Explizite IDs

### Vorteil

* stabil bei Umformulierungen
* stabil bei Verschieben innerhalb der Datei
* robust für Agentenpflege
* sauberer Sidecar-Key

### Nachteil

* zusätzlicher Markdown-Ballast
* CLI muss IDs erzeugen/pflegen
* User/Agent kann IDs versehentlich duplizieren

### Entscheidung

Explizite IDs sind Pflicht.

## 20.2 Sidecar JSON statt SQLite

### Vorteil

* Git-freundlich
* diffbar
* einfach zu verstehen
* portabel
* keine DB-Abhängigkeit

### Nachteil

* schlechter für komplexe Queries
* schlechter für Historie
* weniger robust bei parallelen Writes
* größere Sidecars bei vielen Karten

### Entscheidung

Sidecar JSON ist für MVP Pflicht.

## 20.3 SM-2 statt FSRS

### Vorteil

* sehr einfach
* deterministisch
* schnell implementiert
* keine komplexen Parameter
* keine externen Abhängigkeiten

### Nachteil

* weniger modern als FSRS
* potenziell schlechtere Scheduling-Qualität

### Entscheidung

SM-2 im MVP, Scheduler-Interface für FSRS vorbereiten.

## 20.4 Kein TUI im MVP

### Vorteil

* Core bleibt sauber
* Agentenworkflow steht im Fokus
* weniger Komplexität
* bessere Testbarkeit

### Nachteil

* direkte Mensch-Tool-UX ist nüchtern
* manuelles Lernen ohne Agent weniger komfortabel

### Entscheidung

Headless only im MVP.

---

## 21. Open Questions

Zum aktuellen Stand keine blockierenden Fragen.

Bewusste spätere Entscheidungen:

1. Wann Textual-TUI ergänzen?
2. Wann Tags/Filter ergänzen?
3. Wann FSRS ergänzen?
4. Ob MCP benötigt wird?
5. Ob Review-Historie später gespeichert werden soll?
6. Ob Rubrics strukturiert werden sollen?
7. Ob User-Antworten optional gespeichert werden sollen?

---

## 22. MVP Scope Summary

### Must Have

* Python CLI
* Headless operation
* Markdown Decks
* Eine Datei = ein Deck
* `#flashcard`
* Auto Mode
* explizite Card-IDs
* JSON Sidecars
* `deck create`
* `scan`
* `validate`
* `normalize`
* `next`
* `review`
* `stats`
* `--show-answer`
* `--limit`
* `--format json`
* SM-2
* Scheduler Interface
* Tests

### Must Not Have

* TUI
* Neovim
* MCP
* HTTP API
* Tags/Filter
* Rubric-Datenmodell
* User-Antwortspeicherung
* Review-Historie
* FSRS
* Anki
* Cloud Sync

---

## 23. Recommended Implementation Milestones

## Milestone 1: Project Skeleton

* Python package setup
* CLI entrypoint
* config loading
* basic command structure
* tests scaffold

## Milestone 2: Deck + Sidecar

* `init`
* `deck create`
* sidecar path convention
* JSON load/save
* atomic writes

## Milestone 3: Markdown Parser

* heading parser
* `#flashcard`
* Auto Mode
* ID extraction
* answer extraction
* frontmatter/code-block handling

## Milestone 4: Validate + Normalize

* missing ID detection
* duplicate ID detection
* empty answer detection
* orphaned sidecar detection
* optional ID generation with `--write`

## Milestone 5: Scheduler

* scheduler interface
* SM-2 implementation
* due detection
* new card state

## Milestone 6: Next + Review

* `next --deck`
* `next --limit`
* `next --show-answer`
* `review --deck --card-id --rating`
* sidecar state updates

## Milestone 7: Stats + JSON Output

* global stats
* deck stats
* JSON schemas
* stable output tests

## Milestone 8: Documentation

* README
* Agent usage guide
* Markdown authoring guide
* Best practices for agent grading
* Examples

---

## 24. README Best Practices to Include Later

### 24.1 Agent Prompting Pattern

```text
You are helping the user study flashcards.

Use `recall next --deck <deck> --limit <n> --show-answer` to retrieve cards.
Ask the user only the question.
Do not reveal the answer before the user responds.
After the user responds, compare their answer against the expected answer.
Rate the response as:
- again: incorrect or not remembered
- hard: partially correct or very uncertain
- good: correct with effort
- easy: complete and confident

Then call:
recall review --deck <deck> --card-id <id> --rating <rating>
```

### 24.2 Card Authoring Guidelines

Good cards should be:

* atomic
* specific
* unambiguous
* answerable from memory
* not too broad
* written in the User's own language
* stable enough that IDs do not need frequent changes

### 24.3 Markdown Example

```markdown
## Was ist Eventual Consistency? #flashcard
<!-- recall:id=architecture-eventual-consistency -->

Eventual Consistency bedeutet, dass ein verteiltes System nach einer gewissen Zeit ohne weitere Schreibvorgänge konsistent wird.

Hinweise für Agentenbewertung:
- Muss Verzögerung der Konsistenz erwähnen.
- Muss verteilten Kontext zumindest implizit verstehen.
- Muss nicht CAP-Theorem nennen.
```

Das CLI behandelt alles nach der ID bis zum nächsten Heading als Antworttext.
