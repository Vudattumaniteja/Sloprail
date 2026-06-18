# Tasks - Sloprail

## Phase 1: Contract Harness

- [x] Add canonical Station Folder fixture without HTML preview.
- [x] Implement Station Handoff Validation for required files and path references.
- [x] Validate one Source Video per project.
- [x] Validate non-overlapping Station Target Windows.
- [x] Validate Station-Level Note exists.
- [x] Validate explicit Partial Station Context when context files are missing.

## Phase 2: Frame Evidence

- [x] Extract `source-window.mp4` with original audio.
- [x] Sample Target Window frames at 2 fps.
- [x] Implement perceptual-hash distance calculation.
- [x] Implement Representative Candidate Selection with cheap quality signals.
- [x] Write `visual-evidence/frame-collapse-report.json`.
- [x] Generate clean Representative Frames.
- [x] Generate Marked Frames, including `no_visual_markup` copies when needed.
- [x] Generate `temporal-strip.png` with Embedded Timing Labels.

## Phase 3: Agent Handoff

- [ ] Build Visual Canvas interaction for selecting a Representative Frame.
- [ ] Let the human draw Visual Markup on the selected Representative Frame.
- [ ] Save the resulting Marked Frame without mutating the clean Representative Frame.
- [x] Generate Station `README.md` using the locked first-read brief.
- [x] Generate `station.json` with source time, station-local time, Coverage Spans, Media Properties, and Read Boundary.
- [x] Snapshot Station Context into the Station Folder.
- [x] Add Agent output contract docs to README.
- [ ] Lock Station editing while an Agent Action is active.

## Phase 4: Agent Output Validation

- [x] Validate `agent-output/output.json`.
- [x] Accept merge only for `status=completed`.
- [x] Require `agent-output/replacement-render.mp4` for completed outputs.
- [x] Probe Replacement Render Media Properties.
- [x] Enforce duration tolerance of +/-0.05s.
- [x] Preserve Agent Render Notes.

## Phase 5: ffmpeg Merge

- [x] Probe Source Video Media Properties.
- [x] Normalize Replacement Render to Source Video resolution/fps/encoding as needed.
- [x] Preserve original Source Video audio.
- [x] Merge one Station into the Source Video.
- [x] Write `merge-output/merged-output.mp4`.
- [x] Write `merge-report.json`.
- [x] Write `normalization-report.md`.

## Phase 6: Review Loop

- [x] Add Human Review Notes with station-local and source time.
- [x] Record FPS, visual, and general issue categories.
- [x] Keep normalization damage as human-reviewed evidence, not auto-fix.
- [x] Document rerun workflow after a bad Replacement Render.
- [x] Run first fixture-backed end-to-end Station demo.
