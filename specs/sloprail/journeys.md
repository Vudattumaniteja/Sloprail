# Journeys - Sloprail

## Journey: Create a Station

1. Open one Source Video.
2. Select a Target Window.
3. Sloprail extracts a source-window and samples frames.
4. Sloprail performs Temporal Frame Deduplication.
5. Human adds Visual Markup and a Station-Level Note.
6. Sloprail creates a Temporal Strip with Embedded Timing Labels.
7. Sloprail snapshots Station Context.
8. Station Handoff Validation passes.
9. Human opens the Station Folder in an agent workspace.

## Journey: Merge Completed Agent Work

1. Agent writes `agent-output/replacement-render.mp4`.
2. Agent writes `output.json` and `render-notes.md`.
3. Sloprail validates completed output.
4. ffmpeg probes Source Video and Replacement Render.
5. ffmpeg normalizes replacement visuals if needed.
6. ffmpeg preserves original audio and writes Merged Output.
7. Human reviews and writes Human Review Notes if needed.
