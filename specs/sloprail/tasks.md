# Tasks - Sloprail

## Phase 1: Contract Harness

- [ ] Add canonical Station Folder fixture without HTML preview.
- [ ] Implement Station Handoff Validation for required files and path references.
- [ ] Validate one Source Video per project.
- [ ] Validate non-overlapping Station Target Windows.
- [ ] Validate Station-Level Note exists.
- [ ] Validate explicit Partial Station Context when context files are missing.

## Phase 2: Frame Evidence

- [ ] Extract `source-window.mp4` with original audio.
- [ ] Sample Target Window frames at 2 fps.
- [ ] Implement perceptual-hash distance calculation.
- [ ] Implement Representative Candidate Selection with cheap quality signals.
- [ ] Write `visual-evidence/frame-collapse-report.json`.
- [ ] Generate clean Representative Frames.
- [ ] Generate Marked Frames, including `no_visual_markup` copies when needed.
- [ ] Generate `temporal-strip.png` with Embedded Timing Labels.

## Phase 3: Agent Handoff

- [ ] Generate Station `README.md` using the locked first-read brief.
- [ ] Generate `station.json` with source time, station-local time, Coverage Spans, Media Properties, and Read Boundary.
- [ ] Snapshot Station Context into the Station Folder.
- [ ] Add Agent output contract docs to README.
- [ ] Lock Station editing while an Agent Action is active.

## Phase 4: Agent Output Validation

- [ ] Validate `agent-output/output.json`.
- [ ] Accept merge only for `status=completed`.
- [ ] Require `agent-output/replacement-render.mp4` for completed outputs.
- [ ] Probe Replacement Render Media Properties.
- [ ] Enforce duration tolerance of +/-0.05s.
- [ ] Preserve Agent Render Notes.

## Phase 5: ffmpeg Merge

- [ ] Probe Source Video Media Properties.
- [ ] Normalize Replacement Render to Source Video resolution/fps/encoding as needed.
- [ ] Preserve original Source Video audio.
- [ ] Merge one Station into the Source Video.
- [ ] Write `merge-output/final-station-<id>.mp4`.
- [ ] Write `merge-report.json`.
- [ ] Write `normalization-report.md`.

## Phase 6: Review Loop

- [ ] Add Human Review Notes with station-local and source time.
- [ ] Record FPS, visual, and general issue categories.
- [ ] Keep normalization damage as human-reviewed evidence, not auto-fix.
- [ ] Document rerun workflow after a bad Replacement Render.
