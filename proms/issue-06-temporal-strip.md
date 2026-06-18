# Prompt: Issue #6 - Representative Frames, Marked Frames, And Temporal Strip

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/6
Blocked by: #5

## Mission

Generate the visual evidence an agent will inspect: clean Representative Frames, Marked Frames, and a non-HTML `temporal-strip.png` with Embedded Timing Labels.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `specs/sloprail/specs/core.md`
4. GitHub issue #6

## Branch

```powershell
git checkout -b feature/issue-06-temporal-strip
```

## Engineering Approach

- Use **golden-image or golden-metadata tests** where stable enough.
- Use **contract-first development** for `station.json` Coverage Span links.
- Use **fixture-driven testing** for marked and unmarked frames.
- Use **outside-in validation**: the generated Station should pass Station Handoff Validation.

## Build Scope

- Write clean Representative Frames.
- Write corresponding Marked Frames.
- Preserve Visual Markup as image files, not semantic drawing JSON.
- Create explicit `no_visual_markup` status when a Marked Frame is a clean copy.
- Render `visual-evidence/temporal-strip.png`.
- Draw Embedded Timing Labels for span id, source time, station-local time, and duration.
- Link all evidence from `station.json`.

## Out Of Scope

- HTML preview pages.
- Browser drawing UX polish.
- Agent output validation.
- Merge automation.

## Verification

```powershell
py scripts/validate_project.py
```

Add tests that prove the Temporal Strip and evidence references are created.

## Done Criteria

- A fresh agent can inspect `temporal-strip.png` and understand timing.
- Clean and marked frames are both available.
- Commit and push the branch.
