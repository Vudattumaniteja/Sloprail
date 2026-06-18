# Prompt: Issue #1 - Sloprail V1 Product PRD Guard

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/1

## Mission

Use this prompt when a session needs to maintain or enforce the Sloprail V1 product boundary. This is a governance prompt, not a feature implementation prompt. Your job is to keep implementation work aligned with the product PRD.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/prds/sloprail-v1-prd.md`
4. `specs/sloprail/proposal.md`
5. `specs/sloprail/design.md`
6. GitHub issue #1 and comments

## Work Rules

- Do not write broad product code from this prompt alone.
- Use this prompt to update or verify PRD language, scope boundaries, and acceptance criteria.
- Keep V1 focused on the Visual Canvas, Station Folders, external Agent Actions, and ffmpeg Normalizing Merge.
- Preserve the non-HTML v1 contract.
- If an implementation issue conflicts with this PRD, update the issue or ask for a scope decision before coding.

## Recommended Approach

- Use **contract-first development**: treat the PRD and `CONTEXT.md` as the boundary.
- Use **risk-based review**: focus on scope creep into agent orchestration, full video editing, audio editing, batch merge, and model-based frame reduction.
- Use **traceability review**: each implementation issue should map back to at least one PRD user story.

## Done Criteria

- PRD and spec docs remain consistent.
- Any scope change is explicit and committed.
- `py scripts/validate_project.py` passes.
- Changes are committed on a branch and pushed for review.
