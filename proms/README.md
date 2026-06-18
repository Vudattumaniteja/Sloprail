# Sloprail Proms

`proms/` contains launch prompts for fresh Codex, Plot Code, Claude Code, or similar sessions. Each file is tied to one GitHub issue. Open a new agent session, point it at one prompt file, and say: "implement this."

## How To Use

1. Start a fresh agent session in the Sloprail repository.
2. Ask the agent to read one prompt file, for example `proms/issue-03-station-folder-validator.md`.
3. Tell it to implement exactly that issue.
4. The agent should create a feature branch, work test-first where practical, run validation, commit, and push.
5. If running multiple prompts in parallel, use separate branches and avoid assigning prompts that touch the same files at the same time.

## Prompt Index

- [issue-01-product-prd.md](issue-01-product-prd.md) - product PRD governance and scope guard.
- [issue-02-spec-coordinator-overlap.md](issue-02-spec-coordinator-overlap.md) - spec-coordinator overlap governance.
- [issue-03-station-folder-validator.md](issue-03-station-folder-validator.md) - Station Folder fixture and validation.
- [issue-04-source-window-manifest.md](issue-04-source-window-manifest.md) - source-window extraction, README, and station manifest.
- [issue-05-frame-collapse-report.md](issue-05-frame-collapse-report.md) - perceptual-hash Frame Collapse evidence.
- [issue-06-temporal-strip.md](issue-06-temporal-strip.md) - Representative Frames, Marked Frames, and Temporal Strip.
- [issue-07-agent-output-validator.md](issue-07-agent-output-validator.md) - agent-output validation before merge.
- [issue-08-normalizing-merge.md](issue-08-normalizing-merge.md) - ffmpeg Normalizing Merge.
- [issue-09-human-review-notes.md](issue-09-human-review-notes.md) - Human Review Notes.
- [issue-10-e2e-station-demo.md](issue-10-e2e-station-demo.md) - first fixture-backed HITL demo.
- [issue-20-visual-canvas-markup.md](issue-20-visual-canvas-markup.md) - human Visual Canvas annotation and Marked Frame saving.

## Engineering Approaches To Apply

- **Test-driven development:** write or tighten the failing validator/test first, implement the smallest code that passes, then refactor.
- **Tracer bullet development:** deliver a thin end-to-end path that proves the behavior, not a broad unfinished layer.
- **Contract-first development:** treat `CONTEXT.md`, `AGENTS.md`, `station.json`, and issue acceptance criteria as contracts.
- **Fixture-driven testing:** use small deterministic Station Folder and media fixtures rather than ad hoc manual files.
- **Characterization testing:** when touching existing behavior, capture current behavior before changing it.
- **Golden-file testing:** use stable expected JSON/Markdown outputs where folder contracts matter.
- **Outside-in testing:** validate user-visible folder and media outcomes before internals.
- **Risk-based testing:** put stronger tests around duration tolerance, path validation, non-overlap, and merge reports.
- **HITL review:** use human-in-the-loop only where visual quality judgment is genuinely required.
- **Interaction-first slicing:** when a human action creates core evidence, give that interaction its own vertical slice rather than hiding it inside downstream generation.

## Default Agent Rules

- Read `AGENTS.md`, `CONTEXT.md`, `.harness/PROGRESS.md`, and the linked GitHub issue first.
- Do not change Sloprail vocabulary without updating `CONTEXT.md`.
- Keep v1 non-HTML unless a prompt explicitly changes scope.
- Prefer `py scripts/validate_project.py` on this Windows workstation.
- Do not commit local `prototype-station-001/`.
- Push a branch; do not merge to `main` unless explicitly asked.
