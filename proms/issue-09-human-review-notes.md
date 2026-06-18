# Prompt: Issue #9 - Human Review Notes

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/9
Blocked by: #8

## Mission

Add Human Review Notes for Replacement Render or Merged Output review. Notes should capture station-local time, matching Source Video time, category, and the reviewer observation.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/prds/sloprail-v1-prd.md`
4. GitHub issue #9

## Branch

```powershell
git checkout -b feature/issue-09-human-review-notes
```

## Engineering Approach

- Use **contract-first development** for note format.
- Use **TDD** for timestamp conversion and category validation.
- Use **fixture-driven testing** with Station timing examples.
- Use **HITL awareness**: the system records human judgment but should not auto-fix quality problems.

## Build Scope

- Store Human Review Notes for a Station.
- Record station-local time as primary.
- Record matching Source Video time.
- Support FPS, visual, and general issue categories.
- Allow notes to reference Normalization Report details.
- Document that visible normalization damage is recorded and rerun manually.

## Out Of Scope

- Auto-rerender.
- Automatic visual quality scoring.
- Browser UX polish beyond the note contract.

## Verification

```powershell
py scripts/validate_project.py
```

Run tests for note schema and time conversion.

## Done Criteria

- Human Review Notes are durable and unambiguous.
- Notes can support a future rerun workflow.
- Commit and push the branch.
