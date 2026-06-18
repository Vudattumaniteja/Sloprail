# Prompt: Issue #20 - Visual Canvas Markup Interaction

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/20
Blocked by: #3, #5

## Mission

Implement the missing human interaction slice: opening a Representative Frame in the Visual Canvas, drawing Visual Markup, and saving the result as a Marked Frame. This is the bridge between Frame Collapse and agent-readable visual evidence.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/prds/sloprail-v1-prd.md`
4. GitHub issues #3, #5, #6, and #20

## Branch

```powershell
git checkout -b feature/issue-20-visual-canvas-markup
```

## Engineering Approach

- Use **interaction-first slicing**: the human action that creates Visual Markup deserves its own thin vertical slice.
- Use **TDD where practical** for Marked Frame persistence, Station metadata updates, and `no_visual_markup` behavior.
- Use **contract-first development**: Visual Markup is image evidence, not semantic annotation JSON.
- Use **fixture-driven testing** with a Representative Frame fixture and expected Marked Frame output.
- Use **accessibility-aware UI basics**: controls should be keyboard reachable where practical, even before full design polish.

## Build Scope

- Let the human open or select a Representative Frame for markup.
- Provide basic drawing behavior suitable for circles/freehand marks.
- Save the marked result under `visual-evidence/marked-frames/`.
- Preserve the clean Representative Frame unchanged.
- Update `station.json` to link Representative Frame and Marked Frame.
- Support explicit `no_visual_markup` when no drawing is added.
- Ensure Station Handoff Validation accepts the marked output.

## Out Of Scope

- Semantic annotation types as source of truth.
- Full design-system polish.
- HTML preview pages as Station evidence.
- Agent orchestration.
- Temporal Strip rendering beyond consuming the saved Marked Frames.

## Verification

```powershell
py scripts/validate_project.py
```

Add any UI/persistence tests required by the implementation stack selected in this issue.

## Done Criteria

- A human can create Visual Markup and persist a Marked Frame.
- The Marked Frame is usable by the Temporal Strip issue.
- Clean source evidence remains untouched.
- Commit and push the branch.
