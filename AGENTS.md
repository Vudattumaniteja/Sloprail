# AGENTS.md

## Project Overview
Sloprail is a lightweight browser-oriented visual canvas that prepares Station Folders for AI agents to create replacement renders for selected Source Video windows.

## Tech Stack
- Runtime: Python 3.11+ for validation and local automation scripts
- Media tools: ffmpeg and ffprobe for Source Video probing, window extraction, normalization, and merge
- Frontend: Browser-based app planned; no framework selected in this repo yet
- Data format: Markdown, JSON, image files, and video files

## Quick Start
- Install: `make setup`
- Run tests: `make test`
- Full verification: `make check`
- Windows fallback verification: `py scripts/validate_project.py`
- Clean generated temporary files: `make clean`

## Hard Constraints
1. Use the vocabulary in `CONTEXT.md`; do not invent parallel terms for Station, Target Window, Visual Markup, or Replacement Render.
2. V1 has one Source Video per project.
3. V1 Stations must not overlap in source time.
4. V1 Station Folders are evidence and instruction packets only; they do not run agents.
5. V1 does not include an HTML preview contract.
6. Visual Markup is preserved as marked image files, not semantic drawing JSON.
7. A Station-Level Note is required before handoff.
8. Station Handoff Validation must pass before agent work.
9. Agent Actions should read only the Station Folder unless the human explicitly expands context.
10. Agents must write outputs under `agent-output/`.
11. Only `status=completed` Station outputs can be merged.
12. Replacement Render duration must match the Target Window within +/-0.05s.
13. ffmpeg merge preserves original audio and replaces visuals only.
14. Normalizing Merge must record all media property changes in a Normalization Report.
15. DINO/DINOv3 or other vision-model reduction is out of scope for the v1 baseline.

## Topic Docs
- [Domain Glossary](CONTEXT.md) - Read before changing product language or Station contracts.
- [Sloprail V1 PRD](docs/prds/sloprail-v1-prd.md) - Read before changing product scope.
- [Spec Coordinator Overlap PRD](docs/prds/spec-coordinator-overlap-prd.md) - Read before changing spec-generation or handoff behavior.
- [OpenSpec Bundle](specs/sloprail/) - Read when planning implementation tasks.

## Session Workflow
- Clock in: read `.harness/PROGRESS.md`, `.harness/DECISIONS.md`, and `CONTEXT.md`.
- Pick one feature from `.harness/feature_list.json`; keep WIP at one feature per agent.
- Before editing contracts, update the glossary or PRD first.
- Clock out: run `make check`, update `.harness/PROGRESS.md`, and commit completed work.
