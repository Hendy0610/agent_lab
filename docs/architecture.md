# Architektur

## Systemübersicht

```
Hendrik (Fachliche Freigabe)
    │
    ▼
Requirements Agent (Orchestrator)
    │
    ├─► GitHub Issues (Artefakte)
    │
    ▼
Developer Agent
    │
    ├─► Feature Branches
    ├─► Commits
    └─► Pull Requests
            │
            ▼
    QA & Architecture Agent
            │
            ├─► APPROVED → Requirements Agent → Showcase → Hendrik → Merge
            ├─► CHANGES_REQUESTED → Developer Agent
            └─► BLOCKED → Developer Agent / Hendrik
```

## Zugriffsrechte

### Requirements Agent

- Issues lesen, erstellen, bearbeiten
- Issue-Kommentare lesen und schreiben
- Labels setzen und entfernen
- PRs lesen

### Developer Agent

- Issues lesen
- Branches erstellen
- Code ändern, Commits erstellen
- Pull Requests erstellen und aktualisieren
- PR-Kommentare lesen und schreiben
- nach Freigabe PRs mergen

### QA & Architecture Agent

- Issues lesen
- PRs lesen, Diffs lesen, Code lesen
- Tests/Checks lesen
- PR Reviews oder Kommentare schreiben
- Labels setzen

## Systemgrenze

Alle Agenten arbeiten ausschließlich auf:

```
Owner: Hendy0610
Repository: agent_lab
URL: https://github.com/Hendy0610/agent_lab
Default Branch: main
```

Andere Repositories dürfen nicht gelesen, verändert oder referenziert werden, außer Hendrik gibt dies ausdrücklich frei.
