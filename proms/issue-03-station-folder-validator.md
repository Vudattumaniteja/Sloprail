# Prompt: Issue #3 - Canonical Station Folder Fixture And Validator

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/3

## Mission

Implement the first real Sloprail tracer bullet: a canonical non-HTML Station Folder fixture plus Station Handoff Validation. This should prove the folder contract before media processing exists.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/prds/sloprail-v1-prd.md`
4. `specs/sloprail/specs/core.md`
5. GitHub issue #3

## Branch

Create a branch like:

```powershell
git checkout -b feature/issue-03-station-folder-validator
```

## Engineering Approach

- Use **TDD**: write failing validation cases first, then implement the validator.
- Use **fixture-driven testing**: create small deterministic valid and invalid Station Folder fixtures.
- Use **contract-first development**: the validator should encode the v1 contract from `CONTEXT.md` and issue #3.
- Use **golden-file testing** where expected validation reports are useful.

## Build Scope

- Canonical Station Folder fixture with no HTML preview.
- Validation for required files.
- Validation for `notes.md` presence and non-empty intent.
- Validation for one Source Video per project.
- Validation for non-overlapping Station Target Windows.
- Validation for explicit Partial Station Context.
- Validation that `station.json` path references resolve.

## Out Of Scope

- Frame Collapse.
- ffmpeg extraction or merge.
- Browser UI.
- Agent execution.

## Verification

Run:

```powershell
py scripts/validate_project.py
```

Add any new test command to `AGENTS.md` or the harness if needed.

## Done Criteria

- Issue #3 acceptance criteria are satisfied.
- Tests cover both valid and invalid Station Folders.
- Project validation passes.
- Commit and push the branch.
