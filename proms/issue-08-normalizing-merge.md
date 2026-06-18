# Prompt: Issue #8 - ffmpeg Normalizing Merge

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/8
Blocked by: #7

## Mission

Implement the deterministic one-Station merge path. Agents create Replacement Renders; Sloprail automation validates and merges them with ffmpeg while preserving original audio.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `specs/sloprail/design.md`
4. GitHub issue #8

## Branch

```powershell
git checkout -b feature/issue-08-normalizing-merge
```

## Engineering Approach

- Use **fixture-driven integration tests** with tiny videos.
- Use **outside-in testing**: verify the Merged Output, reports, duration, and audio behavior.
- Use **risk-based testing** for duration mismatch, fps mismatch, resolution mismatch, and missing ffmpeg.
- Use **contract-first development** for `merge-report.json` and `normalization-report.md`.

## Build Scope

- Probe Source Video Media Properties.
- Read validated Replacement Render Media Properties.
- Reject duration mismatch outside +/-0.05s.
- Normalize replacement visuals to Source Video-compatible resolution, fps, pixel format, and encoding as needed.
- Preserve original Source Video audio.
- Merge one Station only.
- Write Merged Output.
- Write `merge-report.json`.
- Write `normalization-report.md`.

## Out Of Scope

- Batch merge.
- Overlapping Station merge.
- Audio replacement.
- Automatic quality repair.

## Verification

```powershell
py scripts/validate_project.py
```

Run ffmpeg integration tests if ffmpeg is available; otherwise skip with an explicit reason and document the missing dependency.

## Done Criteria

- One completed Station can be merged deterministically.
- Normalization evidence is written.
- Commit and push the branch.
