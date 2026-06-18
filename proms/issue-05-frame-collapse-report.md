# Prompt: Issue #5 - Perceptual-Hash Frame Collapse Report

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/5
Blocked by: #4

## Mission

Implement v1 Temporal Frame Deduplication and write `visual-evidence/frame-collapse-report.json`. This slice should produce explainable Frame Collapse evidence without using model-based visual embeddings.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `specs/sloprail/design.md`
4. GitHub issue #5

## Branch

```powershell
git checkout -b feature/issue-05-frame-collapse-report
```

## Engineering Approach

- Use **TDD** for hash-distance behavior and report shape.
- Use **property-style tests** where useful: identical frames should be near-duplicates; clearly different frames should not collapse under the same threshold.
- Use **fixture-driven media tests** with tiny image/frame fixtures.
- Use **contract-first development** for `frame-collapse-report.json`.

## Build Scope

- Sample Target Window candidate frames at 2 fps.
- Calculate perceptual hashes.
- Compare by perceptual-hash distance.
- Implement Representative Candidate Selection using cheap quality signals.
- Reject near-duplicates.
- Write `frame-collapse-report.json` with sampling rate, hash method, thresholds, candidate count, kept count, rejected count, and selection reasons.
- Represent Manual Representative Frame support in the report shape.

## Out Of Scope

- DINO, DINOv3, MobileCLIP, or semantic model reduction.
- Browser drawing UI.
- Temporal Strip rendering.
- Merge automation.

## Verification

```powershell
py scripts/validate_project.py
```

Run new Frame Collapse tests and document any fixture assumptions.

## Done Criteria

- Frame Collapse report is deterministic for fixtures.
- Report fields support downstream Temporal Strip generation.
- Commit and push the branch.
