# Agent Lab

Ein repo-gebundenes Multi-Agent-System, das neue Produktideen kontrolliert in Anforderungen, Implementierung, Qualitätssicherung, Showcase/Bericht und Merge überführt.

## Überblick

Dieses Repository ist das Agent-Lab. Die Agenten entwickeln und optimieren dort schrittweise ihr eigenes Betriebssystem, ihre Prompts, Workflows, Qualitätsregeln, Tests und Automatisierungen.

**Grundprinzip:**
> `Hendy0610/agent_lab` ist die harte Systemgrenze. Issue als Auftrag. Pull Request als Übergabe. Hendrik als fachliche Freigabe. QA-Agent als technisches Gate. Merge auf `main` erst nach beiden Freigaben.

## Agenten

| Agent | Rolle |
|---|---|
| Requirements Agent | Eingangspunkt für Ideen, Orchestrator |
| Developer Agent | Implementierung auf freigegebenen Issues |
| QA & Architecture Agent | Qualitätssicherung und Architekturprüfung |

## Workflow

```text
IDEA_RECEIVED → REQUIREMENTS_DRAFTED → WAITING_FOR_HENDRIK_REQUIREMENTS_APPROVAL
→ APPROVED_FOR_DEVELOPMENT → DEVELOPMENT_IN_PROGRESS → PR_CREATED
→ QA_REVIEW_IN_PROGRESS → QA_APPROVED → SHOWCASE_AND_REPORT_CREATED
→ WAITING_FOR_HENDRIK_RELEASE_APPROVAL → APPROVED_TO_MERGE → MERGED_TO_MAIN → DONE
```

## Dokumentation

- [Workflow](docs/workflow.md)
- [Governance](docs/governance.md)
- [Architektur](docs/architecture.md)

## Agenten-Prompts

- [Requirements Agent](agents/requirements-agent.md)
- [Developer Agent](agents/developer-agent.md)
- [QA & Architecture Agent](agents/qa-architecture-agent.md)

## Templates

- [Issue Template](templates/issue-template.md)
- [Pull Request Template](templates/pull-request-template.md)
- [Showcase Template](templates/showcase-template.md)
- [QA Review Template](templates/qa-review-template.md)
