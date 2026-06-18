# Prompt: Issue #10 - First Fixture-Backed End-To-End Station Demo

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/10
Blocked by: #6, #8, #9

## Mission

Run the first end-to-end Sloprail V1 demo with a fixture Source Video. This is the first HITL slice: it proves the Station workflow mechanically and captures human visual judgment.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `specs/sloprail/tasks.md`
4. GitHub issues #6, #8, #9, and #10

## Branch

```powershell
git checkout -b feature/issue-10-e2e-station-demo
```

## Engineering Approach

- Use **tracer bullet development**: prove one complete path, not every edge case.
- Use **fixture-driven integration testing** with a small Source Video.
- Use **outside-in verification**: generated Station, Replacement Render, Merged Output, and reports must be inspectable.
- Use **HITL review** for visual acceptability and normalization artifacts.

## Build Scope

- Create or reference a small fixture Source Video.
- Create one non-overlapping Station.
- Run Station Handoff Validation.
- Generate Frame Collapse evidence and Temporal Strip evidence.
- Produce or simulate a valid Replacement Render.
- Validate agent output.
- Run ffmpeg Normalizing Merge.
- Write merge evidence.
- Write Human Review Notes.

## Out Of Scope

- Production UI.
- Batch merge.
- Overlap handling.
- Automated visual quality scoring.

## Verification

```powershell
py scripts/validate_project.py
```

Also run the full demo command and record exact output paths and any manual review observations.

## Done Criteria

- One full Station demo is reproducible.
- All reports and review notes are committed or documented.
- Any visual quality concern is recorded, not hidden.
- Commit and push the branch.
