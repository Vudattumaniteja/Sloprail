# Prompt: Issue #4 - Source Window Media And Station Manifest

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/4
Blocked by: #3

## Mission

Implement the first Station generation path from one Source Video Target Window to a Station Folder shell. The output should include `source-window.mp4`, `README.md`, `station.json`, and Station Context snapshots.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `specs/sloprail/design.md`
4. GitHub issues #3 and #4

## Branch

```powershell
git checkout -b feature/issue-04-source-window-manifest
```

## Engineering Approach

- Use **outside-in TDD**: start with a test that creates a Station from a tiny Source Video fixture and validates the resulting folder.
- Use **contract-first development** for `README.md` and `station.json`.
- Use **fixture-driven testing** for Source Video and Station Context.
- Use **thin tracer bullet development**: build the minimum path that generates a valid Station shell.

## Build Scope

- Extract or create `visual-evidence/source-window.mp4` with original audio.
- Generate the locked first-read Station `README.md`.
- Generate `station.json` with Source Video path, Target Window, station-local time, Media Properties when available, and Read Boundary.
- Snapshot Station Context.
- Preserve explicit Partial Station Context behavior.
- Pass the validator from #3.

## Out Of Scope

- Frame Collapse.
- Temporal Strip.
- Agent output validation.
- Merge automation.

## Verification

```powershell
py scripts/validate_project.py
```

Also run any Station generator tests added in this branch.

## Done Criteria

- A generated Station shell validates.
- README and manifest language match `CONTEXT.md`.
- Commit and push the branch.
