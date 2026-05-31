# Governance

## Freigabe-Regeln

### Regel 1: Keine Entwicklung ohne Hendriks Anforderungsfreigabe

Der Developer Agent darf erst starten, wenn der Requirements Agent eine explizite Freigabe dokumentiert hat.

Erlaubte Freigabeformulierung:
- `Approved for development`
- `Freigegeben für Entwicklung`

### Regel 2: Kein Merge ohne QA-OK

Der Developer Agent darf nur mergen, wenn der QA & Architecture Agent `APPROVED` gesetzt hat.

### Regel 3: Kein Merge ohne Hendriks finale Freigabe

Nach QA-OK muss der Requirements Agent Hendrik einen Showcase oder Bericht schicken und um finale Freigabe bitten.

Erlaubte finale Freigabeformulierung:
- `Approved to merge`
- `Freigegeben zum Merge`

### Regel 4: Merge nur auf `main`

Der Merge erfolgt ausschließlich vom freigegebenen Feature-Branch auf `main`.

### Regel 5: Keine stillen Scope-Erweiterungen

Wenn während der Entwicklung neue Anforderungen entstehen, muss der Requirements Agent ein neues oder erweitertes Issue erstellen und Hendrik erneut um Freigabe bitten.

## Technische Schutzmaßnahmen für `main`

- Branch Protection auf `main`
- Pull Request erforderlich
- mindestens 1 Review erforderlich
- direkte Pushes auf `main` verboten
- Status Checks müssen grün sein
- keine Force Pushes
- Secrets Scanning aktivieren
- Merge nur über PR

## Selbstoptimierungsprinzip

Das erste Produkt des Agententeams ist das Agententeam selbst.

Auch Selbstoptimierungen folgen dem normalen Freigabeprozess:

```
Idee → Requirements Draft → Hendriks Entwicklungsfreigabe
→ Implementierung auf Branch → QA Review → Showcase/Bericht
→ Hendriks Merge-Freigabe → Merge auf main
```

## Kommunikationskanal

Die Agenten kommunizieren nicht über freie Chat-Nachrichten, sondern über strukturierte GitHub-Artefakte:

| Artefakt | Bedeutung |
|---|---|
| GitHub Issue | fachlicher Auftrag / Anforderung |
| GitHub Branch | technische Umsetzung |
| Pull Request | Übergabe vom Developer Agent an QA |
| PR Review | Rückmeldung des QA & Architecture Agent |
| Issue-/PR-Kommentare | Agentenkommunikation |
| Labels | Status und Routing |
| Checks | technische Qualitätsnachweise |
