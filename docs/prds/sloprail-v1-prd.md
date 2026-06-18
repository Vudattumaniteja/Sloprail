# Sloprail V1 PRD

## Problem Statement

People can explain desired video changes visually, but current agent workflows force them to translate those changes into weak text prompts. A human may know that a specific screen region, gesture, or visual state needs replacement between `300s-320s`, but Codex, Plot Code, Claude Code, or similar agents need a compact folder of evidence, timing, notes, and context to work reliably without reading the entire Source Video.

## Solution

Sloprail V1 is a lightweight Visual Canvas that creates validated Station Folders. A Station captures one non-overlapping Target Window from one Source Video, reduces it into Representative Frames, preserves human Visual Markup as marked images, writes a Temporal Strip with Embedded Timing Labels, snapshots Station Context, and hands the folder to an external agent workspace. Agents create a Replacement Render, and ffmpeg automation performs a Normalizing Merge that preserves original audio.

## User Stories

1. As a video author, I want to select a Target Window from a Source Video, so that I can focus agent work on one bounded visual problem.
2. As a video author, I want Sloprail to sample frames at 2 fps, so that Station creation stays lightweight.
3. As a video author, I want perceptual-hash Frame Collapse, so that repeated visual states do not waste agent context.
4. As a video author, I want Representative Frames, so that I can inspect the important visual states without reviewing every source frame.
5. As a video author, I want to draw Visual Markup directly on frames, so that my intent is preserved visually instead of forced into fragile annotation types.
6. As a video author, I want a Station-Level Note, so that the agent knows what change is requested.
7. As a video author, I want a Temporal Strip with Embedded Timing Labels, so that agents can understand the full duration from compact evidence.
8. As a video author, I want clean Representative Frames and Marked Frames, so that the agent can compare source evidence against human intent.
9. As a video author, I want `source-window.mp4` to include original audio, so that agents can understand the Station context without editing audio.
10. As a video author, I want full and window transcripts in Station Context, so that agents can use story context and exact local timing.
11. As a video author, I want missing Station Context declared explicitly, so that agents do not invent absent constraints.
12. As a video author, I want Station Handoff Validation, so that incomplete folders are not sent to agents.
13. As an agent operator, I want a README first-read brief, so that I know the Station boundary immediately.
14. As an agent operator, I want a structured `station.json`, so that tools can validate timing, files, and media properties.
15. As an agent operator, I want a Read Boundary, so that the agent does not wander into unrelated project files.
16. As an agent operator, I want to open one Station Folder in Codex, Plot Code, or Claude Code, so that multiple Stations can be worked in parallel manually.
17. As an agent, I want `agent-output/replacement-render.mp4` as the required return file, so that the merge automation can find it reliably.
18. As an agent, I want optional source folders for HyperFrames or other render assets, so that later revisions can inspect how the render was made.
19. As a video author, I want only completed agent outputs to merge, so that blocked or failed attempts cannot corrupt the Merged Output.
20. As a video author, I want ffmpeg to preserve original audio, so that visual replacement does not break narration or music.
21. As a video author, I want ffmpeg to normalize Replacement Render resolution and frame rate when needed, so that agent output can still be merged.
22. As a video author, I want a Normalization Report, so that I can see whether ffmpeg changed fps, resolution, codec, or other Media Properties.
23. As a reviewer, I want Human Review Notes with station-local and source time, so that I can report visual or FPS issues precisely.
24. As a project maintainer, I want one Source Video per v1 project, so that Station generation and merge logic remain stable.
25. As a project maintainer, I want non-overlapping Stations in v1, so that replacement merges do not conflict.

## Implementation Decisions

- Build Sloprail V1 as a Visual Canvas and Station Folder generator, not as an agent runner.
- Use one Source Video per project.
- Forbid overlapping Stations in v1.
- Keep v1 non-HTML: image files, Markdown, JSON, and video files are the contract.
- Use fixed 2 fps Frame Sampling Rate and allow Manual Representative Frames when a human notices a missing moment.
- Use Temporal Frame Deduplication with perceptual-hash distance as the v1 Frame Collapse contract.
- Choose Representative Frames through Representative Candidate Selection, using cheap quality signals and near-duplicate rejection rather than middle-frame selection.
- Store Visual Markup as Marked Frame image files; do not serialize semantic drawing operations.
- Require `notes.md` as the Station-Level Note.
- Create `visual-evidence/temporal-strip.png` with Embedded Timing Labels.
- Snapshot Station Context into the Station Folder; allow partial context only when explicitly declared.
- Require Station Handoff Validation before agent work.
- Agent output contract is `agent-output/replacement-render.mp4`, `agent-output/render-notes.md`, and `agent-output/output.json`.
- Only `status=completed` can be merged.
- Merge one Station at a time in v1.
- Enforce Replacement Render duration within +/-0.05s of the Target Window.
- Use ffmpeg for the final visual replacement, preserve original audio, and write merge evidence.
- Use Normalizing Merge by default and write a Normalization Report.

## Testing Decisions

- Test external behavior through folder validation and media-property probes, not implementation details.
- Validate every generated Station Folder for required files, JSON shape, path references, timing consistency, and non-overlap.
- Validate Frame Collapse by checking candidate counts, kept Representative Frames, rejected near-duplicates, and selection reasons in `frame-collapse-report.json`.
- Validate merge automation by using small fixture videos and verifying duration, audio preservation, Media Properties, and Normalization Report output.
- Validate agent-output handling by accepting only `status=completed` with an existing Replacement Render.

## Out of Scope

- Direct agent orchestration inside Sloprail.
- Built-in multi-agent harness execution.
- HTML preview pages in the v1 contract.
- DINO/DINOv3, MobileCLIP, or other vision-model frame reduction in the v1 baseline.
- Audio editing or generated replacement audio.
- Batch Station merge.
- Overlapping Station merge.
- Multi-Source Video projects.
- Automatic quality repair when normalization causes visible artifacts.

## Further Notes

Sloprail should stay experimental where the model boundary is uncertain. Target Window maximums, normalization quality, and HyperFrames render quality should be measured through prototypes rather than permanently decided in the first implementation.
