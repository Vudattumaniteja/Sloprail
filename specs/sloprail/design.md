# Design - Sloprail

## Architecture Overview

```text
Source Video
  -> Visual Canvas
  -> Target Window
  -> 2 fps sampling
  -> Temporal Frame Deduplication
  -> Representative Frames + Marked Frames
  -> Temporal Strip + Station Context snapshot
  -> Station Folder
  -> external Agent Action
  -> Replacement Render
  -> ffmpeg Normalizing Merge
  -> Merged Output
```

Sloprail V1 should keep human visual work and deterministic media automation separate. The browser-facing Visual Canvas prepares Station Folders. External agents inspect those folders and produce Replacement Renders. Local automation validates and merges completed outputs.

The Station Folder is the contract boundary. It must be readable without opening the whole Source Video and strict enough for automation to validate.

## Tech Stack

| Layer | Pick | Rationale |
|---|---|---|
| Browser UI | Lightweight HTML canvas app, framework undecided | The product needs direct visual markup and timeline controls, but v1 specs should not force a frontend stack yet. |
| Local scripts | Python 3.11+ | Good fit for JSON validation, image processing, and ffmpeg orchestration. |
| Media processing | ffmpeg / ffprobe | Deterministic probing, window extraction, normalization, concat, and audio preservation. |
| Frame reduction | Perceptual hash + Hamming distance | Lightweight, explainable, no model dependency in v1 baseline. |
| Storage | Filesystem folders | Agent workspaces can inspect folders directly. |
| Tests | Scripted validators + fixture media tests | External behavior is folder shape and media output correctness. |

## Data Model Sketch

```text
Project
  SourceVideo
  Station[]

Station
  TargetWindow
  CoverageSpan[]
  StationContextSnapshot
  AgentOutput?
  MergeOutput?

CoverageSpan
  RepresentativeFrame
  MarkedFrame
  Coverage timing
  VisualMarkupStatus
```

## API Surface Sketch

V1 does not require a network API. Local module seams should be:

| Interface | Purpose |
|---|---|
| createStation(project, targetWindow) | Build draft Station evidence from a Source Video range. |
| validateStation(stationFolder) | Enforce Station Handoff Validation. |
| validateAgentOutput(stationFolder) | Accept or reject agent-output. |
| mergeStation(project, stationFolder) | Produce one Merged Output with Normalization Report. |

## Key Decisions

### Decision: Visual Canvas, not agent harness
- **Pick:** Sloprail prepares Station Folders but does not deploy agents in v1.
- **Why:** Codex, Plot Code, and Claude Code already provide agent execution surfaces.
- **Alternatives rejected:** Built-in orchestration - too much scope for v1 and duplicates existing tools.

### Decision: Non-HTML v1 Station contract
- **Pick:** Use image, Markdown, JSON, and video files only.
- **Why:** Agents can inspect these directly and the user explicitly chose non-HTML for v1.
- **Alternatives rejected:** `preview.html` - useful later, but adds another surface and risks hiding information.

### Decision: Perceptual Hash Contract
- **Pick:** Contract says perceptual hash, implementation may start with dHash or another algorithm.
- **Why:** Keeps v1 explainable while avoiding an unnecessary permanent algorithm lock.
- **Alternatives rejected:** DINO/DINOv3 baseline - should remain an experiment after the folder pipeline works.

### Decision: Normalizing Merge
- **Pick:** ffmpeg may normalize Replacement Render resolution, fps, pixel format, and encoding before merge.
- **Why:** Agents and HyperFrames outputs may vary; v1 should capture evidence rather than block all mismatches.
- **Alternatives rejected:** Strict media-property reject by default - useful as an experiment but too brittle as default.

### Decision: Original Audio Preservation
- **Pick:** Preserve Source Video audio for the Target Window.
- **Why:** V1 is visual-only, and original narration/music should continue unchanged.
- **Alternatives rejected:** Replacement audio - out of scope for v1.

## Trade-offs Accepted

- Lightweight frame reduction may miss very fast visual changes - gain: simple v1; cost: Manual Representative Frame escape hatch is needed.
- Normalization can create visible artifacts - gain: forgiving merge; cost: Human Review Notes and Normalization Report must capture issues.
- No HTML preview - gain: simple agent-readable contract; cost: less rich local review surface.
- One-Station merge first - gain: stable implementation; cost: batch workflows wait.

## Risk Register

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Model/agent cannot create high-quality Replacement Render | high | med | Keep render quality experimental and capture Agent Render Notes. |
| Normalization causes choppy motion | med | med | Record fps changes and Human Review Notes; rerun manually. |
| Human forgets to write intent note | med | high | Require Station-Level Note in validation. |
| Missing context causes invented style rules | med | med | Require explicit Partial Station Context declaration. |
| Scope drifts into full editor/harness | high | med | Enforce AGENTS.md and out-of-scope docs. |

## Performance Targets

- Station generation for a 20-second Target Window should stay local and model-free.
- 2 fps sampling should keep candidate frame count small: about 40 candidates for 20 seconds, about 100 for 50 seconds.
- Merge automation should fail fast on missing files or duration mismatch.

## Security & Privacy

- Data classified: local user media, potentially sensitive.
- Secrets management: no secrets required for local Station generation.
- Auth model: N/A for local-first v1.
- Data residency: local filesystem by default.

## Observability Plan

- **Logs:** validation errors, ffmpeg commands, media probes, merge status.
- **Metrics:** candidate frame count, kept frame count, rejected duplicate count, media-property changes, duration delta.
- **Reports:** `frame-collapse-report.json`, `output.json`, `merge-report.json`, `normalization-report.md`.
- **Review:** `Human Review Notes` for visible artifacts.

## Rollout Plan

- Phase 1: Station Folder contract and validator.
- Phase 2: Frame Collapse and Temporal Strip.
- Phase 3: Agent output validator.
- Phase 4: single-Station ffmpeg merge.
- Phase 5: prototype quality experiments across replacement fps/resolution.

## Open Technical Questions

See `open-questions.md`. None block the first contract/validator implementation.
