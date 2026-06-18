# Station station-001

## First Read
This Station Folder is an Agent Work Packet for one Target Window from one Source Video. The Read Boundary is this Station Folder unless the human explicitly expands context.

## Target Window
- Source Video: `source-video-001`
- Source time: `12.000s` to `22.000s`
- Station-local duration: `10.000s`

## Partial Station Context
This Station intentionally omits `design-rules.md`. Do not invent missing design rules; ask the human if the Replacement Render depends on them.

## Required Output
Write Agent Action results under `agent-output/`.

## Human Review Notes
After reviewing a Replacement Render or Merged Output, write station-local observations to `review-notes.json`. Visible normalization damage is recorded as Human Review Notes and rerun manually; Sloprail does not auto-fix review findings.
