# Prompt: Issue #7 - Agent Output Validator

Issue: https://github.com/Vudattumaniteja/Sloprail/issues/7
Blocked by: #3

## Mission

Implement validation for the return package from an external Agent Action. This gate decides whether a Station is eligible for merge.

## Read First

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/prds/sloprail-v1-prd.md`
4. GitHub issue #7

## Branch

```powershell
git checkout -b feature/issue-07-agent-output-validator
```

## Engineering Approach

- Use **TDD** for completed, blocked, failed, and malformed outputs.
- Use **contract-first development** for `agent-output/output.json`.
- Use **risk-based testing** around duration tolerance and missing render files.
- Use **fixture-driven testing** with tiny replacement media or mocked media probes.

## Build Scope

- Validate `agent-output/output.json`.
- Allow `completed`, `blocked`, and `failed` statuses.
- Permit merge only for `status=completed`.
- Require `replacement-render.mp4` and Agent Render Notes for completed outputs.
- Probe Replacement Render Media Properties when the render exists.
- Enforce duration tolerance of +/-0.05s.
- Allow optional HyperFrames/source folders.

## Out Of Scope

- Actually merging video.
- Generating Replacement Renders.
- Agent orchestration.

## Verification

```powershell
py scripts/validate_project.py
```

Run all new validator tests.

## Done Criteria

- Non-completed statuses cannot be merged.
- Completed output is machine-verifiable.
- Commit and push the branch.
