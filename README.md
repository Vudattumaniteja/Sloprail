# Sloprail

Sloprail is a lightweight visual canvas for turning short source-video ranges into agent-readable Station Folders. A Station compresses a target window into representative visual evidence, human markup, timing labels, notes, and project context so Codex, Plot Code, Claude Code, or similar agents can create a replacement render without inspecting the whole video.

## V1 Boundary

- One project has one Source Video.
- Stations are non-overlapping Target Windows, commonly 10-20 seconds and experimentally up to about 50 seconds.
- The Visual Canvas creates evidence-only Station Folders.
- Agents work outside Sloprail by opening Station Folders directly.
- The required agent output is `agent-output/replacement-render.mp4`.
- ffmpeg automation performs visual replacement and preserves original audio.
- V1 uses image, Markdown, JSON, and video files only. No HTML preview is part of the v1 contract.

## Core Flow

1. Upload or register a Source Video.
2. Select a Target Window.
3. Sample at 2 fps and perform perceptual-hash frame reduction.
4. Create Representative Frames, Marked Frames, and a Temporal Strip with embedded timing labels.
5. Save a validated Station Folder with Station Context and a Station-Level Note.
6. Open the Station Folder in an agent workspace.
7. Agent writes `agent-output/replacement-render.mp4`, `render-notes.md`, and `output.json`.
8. Merge automation normalizes replacement media if needed, preserves original audio, and writes a Merged Output.
9. Human review writes `review-notes.json` with station-local time, matching Source Video time, category, and observation. Visible normalization damage is recorded and rerun manually, not auto-fixed.

## Repository Map

- [CONTEXT.md](CONTEXT.md) - domain glossary and v1 language.
- [docs/prds/sloprail-v1-prd.md](docs/prds/sloprail-v1-prd.md) - product PRD synthesized from the planning session.
- [docs/prds/spec-coordinator-overlap-prd.md](docs/prds/spec-coordinator-overlap-prd.md) - PRD for how Sloprail specs overlap with spec-coordinator.
- [specs/sloprail/](specs/sloprail/) - OpenSpec-compatible bundle.
- [proms/](proms/) - prompt files for launching issue-specific agent sessions.
- [AGENTS.md](AGENTS.md) - agent entrypoint and hard constraints.
- [.harness/](.harness/) - harness state and feature tracking.

## Verification

```powershell
make check
```

On this Windows workstation, if `make` is unavailable:

```powershell
py scripts/validate_project.py
```

## Fixture Demo

Run the first fixture-backed end-to-end Station demo:

```powershell
py scripts/run_e2e_station_demo.py --force
```

The command writes `demos/issue-10-e2e-station-demo/demo-report.json` plus the generated Station Folder, Replacement Render, Merged Output, merge evidence, and Human Review Notes.
