# Prompt: Issue #2 - Spec-Coordinator Overlap Boundary

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/2

## Mission

Use this prompt when changing how Sloprail planning artifacts relate to `spec-coordinator`. This is a governance prompt for specs and issue generation, not a product feature prompt.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/prds/spec-coordinator-overlap-prd.md`
4. `specs/sloprail/`
5. GitHub issue #2 and comments

## Work Rules

- Sloprail owns video-agent domain language and Station Folder contracts.
- `spec-coordinator` owns PRD-grade spec shape: `proposal.md`, `specs/`, `design.md`, `tasks.md`, personas, journeys, metrics, out-of-scope, and open questions.
- Do not invent a second Sloprail-only spec format.
- Any implementation issue should remain portable to the coordinator pipeline.

## Recommended Approach

- Use **spec-first development** for planning changes.
- Use **traceability review** to ensure PRDs, OpenSpec files, and GitHub issues agree.
- Use **outside-in validation**: a fresh agent should know what to build by reading the issue plus repo docs.

## Done Criteria

- Spec artifacts remain OpenSpec-compatible.
- Any prompt or issue changes preserve `CONTEXT.md` vocabulary.
- `py scripts/validate_project.py` passes.
- Changes are committed on a branch and pushed for review.
