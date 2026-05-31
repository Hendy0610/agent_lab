# Workflow

## Statusmodell

```text
IDEA_RECEIVED
  ↓
REQUIREMENTS_DRAFTED
  ↓
WAITING_FOR_HENDRIK_REQUIREMENTS_APPROVAL
  ↓
APPROVED_FOR_DEVELOPMENT
  ↓
DEVELOPMENT_IN_PROGRESS
  ↓
PR_CREATED
  ↓
QA_REVIEW_IN_PROGRESS
  ↓
QA_APPROVED
  ↓
SHOWCASE_AND_REPORT_CREATED
  ↓
WAITING_FOR_HENDRIK_RELEASE_APPROVAL
  ↓
APPROVED_TO_MERGE
  ↓
MERGED_TO_MAIN
  ↓
DONE
```

## Alternative Pfade

```text
QA_REVIEW_IN_PROGRESS → CHANGES_REQUESTED → DEVELOPMENT_IN_PROGRESS

WAITING_FOR_HENDRIK_REQUIREMENTS_APPROVAL → REQUIREMENTS_REVISION_REQUESTED → REQUIREMENTS_DRAFTED

WAITING_FOR_HENDRIK_RELEASE_APPROVAL → RELEASE_REVISION_REQUESTED → DEVELOPMENT_IN_PROGRESS oder QA_REVIEW_IN_PROGRESS
```

## GitHub Labels

### Status-Labels

```
status/idea-received
status/requirements-drafted
status/waiting-for-requirements-approval
status/approved-for-development
status/in-development
status/pr-created
status/ready-for-qa
status/qa-in-progress
status/qa-approved
status/changes-requested
status/blocked
status/showcase-ready
status/waiting-for-merge-approval
status/approved-to-merge
status/merged
status/done
```

### Rollen-Labels

```
agent/requirements
agent/developer
agent/qa-architecture
```

### Typ-Labels

```
type/feature
type/bugfix
type/chore
type/refactor
type/documentation
```

### Risiko-Labels

```
risk/low
risk/medium
risk/high
risk/security
risk/privacy
risk/architecture
risk/breaking-change
```

## Kommentar-Kommandos

### Kommandos von Hendrik

```
/approve-development
/request-requirements-changes <Beschreibung>
/reject-requirement <Grund>
/approve-merge
/request-release-changes <Beschreibung>
/do-not-merge <Grund>
```

Deutschsprachige Alternativen:

```
/Freigegeben für Entwicklung
/Anforderungen ändern <Beschreibung>
/Anforderung ablehnen <Grund>
/Freigegeben zum Merge
/Release ändern <Beschreibung>
/Nicht mergen <Grund>
```

### Kommandos des Requirements Agent

```
/assign-to-developer
/request-qa-review
/request-showcase
/merge-approved-by-hendrik
```

### Kommandos des Developer Agent

```
/development-started
/pr-created <PR-Link>
/implementation-updated
/ready-for-qa
/merged-to-main <Commit/PR-Link>
/blocked <Grund>
```

### Kommandos des QA & Architecture Agent

```
/qa-started
/qa-approved
/changes-requested <Beschreibung>
/blocked <Grund>
```

## Branch- und PR-Konventionen

### Branch-Namen

```
feature/<issue-id>-short-description
fix/<issue-id>-short-description
chore/<issue-id>-short-description
```

### Pull-Request-Titel

```
[<Issue-ID>] <Kurzbeschreibung>
```
