# Sloprail Spec-Coordinator Overlap PRD

## Problem Statement

Sloprail needs PRD-grade specs and OpenSpec-compatible bundles, but the project already invokes `spec-coordinator` for that role. If Sloprail invents a parallel spec system, agent work will split across duplicated PRD formats, unclear ownership, and inconsistent task handoffs.

## Solution

Define a clean overlap boundary: Sloprail owns Station evidence, Station Folder contracts, and video replacement domain language. `spec-coordinator` owns PRD-grade spec synthesis, OpenSpec bundle shape, capability specs, tasks, personas, journeys, metrics, and open questions. Sloprail can generate or store specs, but the structure should remain compatible with `spec-coordinator` output.

## User Stories

1. As a project owner, I want Sloprail planning artifacts to match `spec-coordinator` structure, so that build agents can consume them without translation.
2. As a spec writer, I want Sloprail domain language to come from `CONTEXT.md`, so that PRDs do not drift into generic video-editor terms.
3. As a build agent, I want `proposal.md`, `specs/`, `design.md`, and `tasks.md`, so that I can move from planning to implementation.
4. As a build agent, I want acceptance scenarios in Given/When/Then form, so that I can verify behavior without guessing.
5. As a project owner, I want out-of-scope decisions explicit, so that v1 does not expand into an agent harness or full video editor.
6. As a project owner, I want open questions tagged blocking or non-blocking, so that experimentation does not halt basic implementation.
7. As a project owner, I want two PRD tracks, so that product scope and spec-coordinator overlap can be reviewed separately.
8. As a future agent, I want specs to reference Station Folder contracts, so that implementation preserves the handoff model.
9. As a future agent, I want tasks to be phased, so that the first implementation can focus on Station validation before rendering features.
10. As a maintainer, I want Sloprail specs stored in-repo, so that GitHub issues can link to durable artifacts.

## Implementation Decisions

- Use `specs/sloprail/` as the OpenSpec-compatible Sloprail bundle.
- Use `docs/prds/sloprail-v1-prd.md` as the product PRD.
- Use `docs/prds/spec-coordinator-overlap-prd.md` as the spec-governance PRD.
- Treat `CONTEXT.md` as the vocabulary source of truth.
- Keep Sloprail's v1 build tasks in `specs/sloprail/tasks.md`.
- Publish PRDs as GitHub issues with `ready-for-agent` when the private repository exists.
- Do not build a separate Sloprail-specific spec format.

## Testing Decisions

- Validate that PRDs include the expected headings from the `to-prd` template.
- Validate that OpenSpec capability specs include Given/When/Then acceptance scenarios.
- Validate that tasks are implementation-ready and map to v1 constraints.
- Review any generated issue against the in-repo artifact before assignment.

## Out of Scope

- Replacing `spec-coordinator`.
- Creating a custom PRD schema that only Sloprail understands.
- Publishing specs to multiple issue trackers in v1.
- Automatically invoking build-coordinator from inside Sloprail.

## Further Notes

The overlap is intentional: Sloprail contributes precise video-agent domain language, and `spec-coordinator` supplies planning structure. The best result is a spec bundle that feels native to Sloprail but remains portable to the broader coordinator pipeline.
