# Capability: Sloprail V1 Core

Create validated Station Folders from one Source Video and merge one completed Replacement Render back into the video.

## Why this exists

Sloprail exists to convert human visual intent into compact, reliable agent-readable work packets.

## User Stories

- As a **video author**, I want to create a Station from one Target Window so that I can assign a focused visual replacement task.
- As an **agent operator**, I want a validated Station Folder so that Codex, Plot Code, or Claude Code can work without guessing context.
- As a **reviewer**, I want merge and normalization evidence so that I can identify fps, resolution, or duration problems.

## Acceptance Scenarios

### Scenario: Station handoff succeeds

GIVEN a project with one Source Video
AND the human selects a non-overlapping Target Window
AND Station Context is present or explicitly declared partial
WHEN the human saves the Station
THEN Sloprail creates a Station Folder
AND `station.json` references all required evidence files
AND `visual-evidence/temporal-strip.png` exists with Embedded Timing Labels
AND `notes.md` contains a Station-Level Note
AND Station Handoff Validation passes.

### Scenario: Frame Collapse creates representative evidence

GIVEN a Target Window
WHEN Sloprail samples frames at 2 fps
AND applies Temporal Frame Deduplication using perceptual-hash distance
THEN it writes Representative Frames
AND it writes corresponding Marked Frames
AND it writes `visual-evidence/frame-collapse-report.json`
AND the report includes sampling rate, hash method, thresholds, kept counts, rejected counts, and selection reasons.

### Scenario: Agent output can be merged

GIVEN a Station Folder with `agent-output/output.json`
AND `output.json` has `status=completed`
AND `agent-output/replacement-render.mp4` exists
AND its duration matches the Target Window within +/-0.05s
WHEN merge automation runs
THEN ffmpeg inserts the Replacement Render visuals into the Source Video
AND preserves the original Source Video audio
AND writes a Merged Output
AND writes a Normalization Report.

### Error: Station overlaps another Station

GIVEN an existing Station covering `300s-320s`
WHEN the human attempts to save a new Station covering `315s-330s`
THEN Station Handoff Validation fails
AND no agent-ready Station Folder is created.

### Error: Missing note

GIVEN a Station with Visual Markup
BUT no Station-Level Note
WHEN the human attempts handoff
THEN Station Handoff Validation fails
AND the Station remains draft.

### Error: Agent output is blocked

GIVEN `agent-output/output.json` has `status=blocked`
WHEN merge automation runs
THEN the merge is rejected
AND no Merged Output is written.

## Constraints

- **Performance:** V1 should create a Station for a 20-second Target Window without requiring model inference.
- **Security:** Station Folder Read Boundary must be explicit in README.
- **Scale:** One Source Video per project and one Station merge at a time in v1.
- **Accessibility:** Visual Canvas accessibility is planned but not fully specified in this core v1 bundle.
- **Compatibility:** Station Folder files must be usable by standard agent workspaces and plain filesystem tools.

## Out-of-Scope for this capability

- Multi-source projects.
- Overlapping Station merge.
- Direct agent orchestration.
- HTML preview pages.
- Audio replacement.

## Dependencies

- ffmpeg and ffprobe.
- Browser canvas implementation.
- Image-processing library for perceptual hash and temporal strip rendering.
