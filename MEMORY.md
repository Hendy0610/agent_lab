# MEMORY.md — Projektgedächtnis des Agent Lab

Dieses Dokument ist das zentrale, langlebige Gedächtnis des Agent Lab.
Alle Agenten lesen es zu Beginn jeder Aufgabe. Es dokumentiert Projektziel,
Architektur, Governance-Regeln, Entscheidungen und offene Themen.

**Letzte Aktualisierung:** 2026-06-01

---

## Projektziel

`agent_lab` ist ein repo-gebundenes Multi-Agent-System. Es entwickelt und optimiert
schrittweise sein eigenes Betriebssystem sowie Software-Projekte für Hendrik.

Grundprinzip:
> `agent_lab` ist die harte Systemgrenze. Issue als Auftrag. Pull Request als Übergabe.
> Hendrik als fachliche Freigabe. QA-Agent als technisches Gate.
> Merge auf `main` erst nach beiden Freigaben.

---

## Control Plane

`agent_lab` ist die **Control Plane** des gesamten Systems:

- Alle GitHub Actions Workflows leben in `agent_lab`
- Alle Agenten-Skripte (`scripts/`) leben in `agent_lab`
- Neue Projekte bekommen eigene Repositories (`Hendy0610/<projektname>`)
- Die Steuerung, Workflows und Governance bleiben immer in `agent_lab`
- Der `GH_PAT` in `agent_lab` ermöglicht repo-übergreifende Operationen

---

## Kommunikationskanal

**Telegram** ist der primäre Kommunikationskanal zwischen Hendrik und den Agenten.

| Richtung | Was |
|---|---|
| Hendrik → Agenten | Ideen als Freitext, Freigabe-Kommandos |
| Agenten → Hendrik | Benachrichtigungen, Screenshots, Berichte |

Telegram-Kommandos von Hendrik:

| Kommando | Bedeutung |
|---|---|
| Freitext | Neue Idee → GitHub Issue wird erstellt |
| `/approve-development N` | Requirements freigeben |
| `/approve-design N` | Design freigeben |
| `/merge N` | Merge nach QA freigeben |
| `/status` | Offene Issues auflisten |

---

## Die 5 Agenten

### 1. Requirements Agent
- **Trigger:** Neues GitHub Issue (via Telegram oder direkt)
- **Aufgabe:** Analysiert Idee, erstellt strukturierte Anforderungen, klassifiziert Ziel-Repo
- **Klassifizierung:** Agent-Verbesserung → `agent_lab` / Neues Projekt → neues Repo
- **Output:** Anforderungskommentar im Issue, Label `status/waiting-for-requirements-approval`
- **Script:** `scripts/requirements_agent.py`

### 2. Design Agent
- **Trigger:** `/approve-development` Kommentar im Issue
- **Aufgabe:** Generiert Design-Dokument + HTML/CSS Mockup, Screenshot via Playwright
- **Output:** Design-Kommentar im Issue, Screenshot als Telegram-Bild
- **Script:** `scripts/design_agent.py`

### 3. Developer Agent
- **Trigger:** `/approve-design N` Kommentar im Issue
- **Aufgabe:** Erstellt Feature-Branch, implementiert Code mit Claude Tool Use, pusht, erstellt PR
- **Bei neuem Projekt:** Erstellt Ziel-Repo automatisch via `GH_PAT`
- **Output:** Feature-Branch + PR im Ziel-Repo, Kommentar `/ready-for-qa` im Issue
- **Script:** `scripts/developer_agent.py`

### 4. QA & Architecture Agent
- **Trigger:** `/ready-for-qa` Kommentar im Issue
- **Aufgabe:** Liest PR-Diff + Anforderungen + CI-Status + MEMORY.md, erstellt Review
- **Ergebnis:** `APPROVED`, `CHANGES_REQUESTED` oder `BLOCKED`
- **Blockiert wenn:** CI fehlschlägt oder noch läuft
- **Script:** `scripts/qa_agent.py`

### 5. Merge Agent
- **Trigger:** `/approve-merge` oder `/merge N` (via Telegram)
- **Aufgabe:** Prüft QA-Label + CI-Status, merged PR auf `main`, schließt Issue
- **Blockiert wenn:** QA nicht APPROVED oder CI rot
- **Implementierung:** Inline Python in `.github/workflows/merge-agent.yml`

---

## Workflow: Idee bis Merge

```
Telegram: Freitext-Idee
        ↓
[Requirements Agent] → Anforderungsanalyse im Issue
        ↓
★ FREIGABE: /approve-development N  ← Hendrik
        ↓
[Design Agent] → Design-Dokument + Screenshot → Telegram
        ↓
★ FREIGABE: /approve-design N  ← Hendrik
        ↓
[Developer Agent] → Feature-Branch + Code + PR
        ↓
[CI] → Syntax, Lint, Tests (automatisch)
        ↓
[QA Agent] → Review gegen Akzeptanzkriterien
        ↓
[Requirements Agent] → Showcase/Freigabeanfrage
        ↓
★ FREIGABE: /merge N  ← Hendrik
        ↓
[Merge Agent] → Merge auf main, Issue geschlossen
```

**Drei menschliche Freigaben:**
1. `/approve-development N` — nach Requirements
2. `/approve-design N` — nach Design
3. `/merge N` — nach QA + Showcase

---

## Sicherheitsgates

| Gate | Wo | Was wird geprüft |
|---|---|---|
| CI grün | GitHub Actions `ci.yml` | Syntax, Lint, Tests |
| QA APPROVED | `qa_agent.py` | Akzeptanzkriterien, Architektur, Security |
| Branch Protection | GitHub `main` | PR erforderlich, CI-Checks erforderlich, kein Force Push |
| Merge-Sperre | `merge-agent.yml` | QA-Label + CI-Status vor Merge |
| Keine direkten main-Pushes | Branch Protection | Technisch blockiert durch GitHub |

---

## Governance-Grundregeln

1. **Keine Entwicklung ohne Hendriks Freigabe** — Developer Agent startet erst nach `/approve-development`
2. **Kein Merge ohne QA-OK** — Merge Agent prüft `status/qa-approved` Label
3. **Kein Merge ohne Hendriks finale Freigabe** — `/merge N` erforderlich
4. **Merge nur auf `main`** — Feature-Branch → main, kein anderer Zielbranch
5. **Keine stillen Scope-Erweiterungen** — neue Anforderungen = neues Issue + neue Freigabe

---

## Architekturentscheidungen

| Entscheidung | Gewählt | Begründung |
|---|---|---|
| Memory-Speicher | `MEMORY.md` im Repo | Versioniert, menschenlesbar, kein externer Dienst |
| Kommunikationskanal | Telegram Bot | Mobil, asynchron, kein GitHub-Login nötig |
| Agent-Hosting | GitHub Actions | Kein eigener Server, kostenlos, direkte Repo-Integration |
| Modell | `claude-sonnet-4-6` | Aktuelles Modell, gutes Preis-/Leistungsverhältnis |
| Repo-Strategie | Ein Repo pro Projekt | Saubere Trennung, `agent_lab` bleibt Control Plane |
| Screenshot-Tool | Playwright + Chromium | Läuft in GitHub Actions, kein externer Service |
| CI-Checks | flake8 + pytest | Leichtgewichtig, keine komplexe Pipeline nötig |
| Branch Protection | Nur `main` | Feature-Branches müssen für Developer Agent offen bleiben |

---

## Offene Themen

- **State-Verwaltung:** Telegram-Offset wird via GitHub Actions Cache gespeichert — fragil bei parallelen Runs
- **Telegram Bot Design:** Aktuell Polling alle 2 Minuten — Webhook wäre reaktionsschneller, braucht aber Server
- **Repo-Erstellung:** Neue Projekt-Repos werden public erstellt — Privacy-Implikationen prüfen
- **Screenshot-Speicherung:** Design-Screenshots werden im Repo unter `.github/designs/` gespeichert — wächst unbegrenzt
- **Secret Management:** Alle Secrets in `agent_lab` hinterlegt — bei vielen Projekten ggf. GitHub Organization sinnvoll
- **Error Notifications:** Wenn ein Workflow fehlschlägt, bekommt Hendrik keine Telegram-Nachricht — blinder Fleck

---

## Wann MEMORY.md aktualisiert werden soll

Agenten aktualisieren `MEMORY.md` wenn:

- Eine neue Architekturentscheidung getroffen wurde
- Ein offenes Thema gelöst wurde (aus der Liste entfernen)
- Ein neues offenes Thema entsteht (in die Liste aufnehmen)
- Ein neuer Agent hinzugefügt oder ein bestehender grundlegend geändert wurde
- Governance-Regeln geändert wurden
- Der Workflow sich strukturell ändert

**Wer aktualisiert:** Der Developer Agent fügt MEMORY.md-Updates in seinen Commit ein, wenn die Anforderungen eine architekturelle Änderung enthalten. Der QA Agent weist darauf hin, wenn ein PR ein Memory-Update auslösen sollte.
