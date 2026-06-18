# Issue #10 End-to-End Station Demo

## Command

```powershell
py scripts/run_e2e_station_demo.py --force
```

## Result

- Status: completed
- Station Handoff Validation: passed with 0 issues
- Agent Output Validation: passed with 0 issues
- Merge allowed: true
- Merged Output original audio preserved: true
- Source Video duration: 5.000s
- Target Window: 1.000s to 3.000s
- Replacement Render duration: 2.000s
- Merged Output duration: 5.015s

## Output Paths

- Demo report: `demos/issue-10-e2e-station-demo/demo-report.json`
- Fixture Source Video: `demos/issue-10-e2e-station-demo/source-video.mp4`
- Station Folder: `demos/issue-10-e2e-station-demo/stations/station-e2e-001`
- Source Window: `demos/issue-10-e2e-station-demo/stations/station-e2e-001/visual-evidence/source-window.mp4`
- Frame Collapse Report: `demos/issue-10-e2e-station-demo/stations/station-e2e-001/visual-evidence/frame-collapse-report.json`
- Temporal Strip: `demos/issue-10-e2e-station-demo/stations/station-e2e-001/visual-evidence/temporal-strip.png`
- Replacement Render: `demos/issue-10-e2e-station-demo/stations/station-e2e-001/agent-output/replacement-render.mp4`
- Merge Report: `demos/issue-10-e2e-station-demo/stations/station-e2e-001/merge-output/merge-report.json`
- Normalization Report: `demos/issue-10-e2e-station-demo/stations/station-e2e-001/merge-output/normalization-report.md`
- Merged Output: `demos/issue-10-e2e-station-demo/stations/station-e2e-001/merge-output/merged-output.mp4`
- Human Review Notes: `demos/issue-10-e2e-station-demo/stations/station-e2e-001/review-notes.json`

## Human Review Observations

- Replacement Render is synthetic fixture media, so visual acceptability is limited to mechanical inspectability.
- Normalization changes are expected and recorded as HITL evidence, not auto-fixed.

## Rerun Workflow

If a Replacement Render is visually unacceptable, update or replace `agent-output/replacement-render.mp4`, rewrite `agent-output/render-notes.md` and `agent-output/output.json` if needed, run `py scripts/validate_agent_output.py demos/issue-10-e2e-station-demo/stations/station-e2e-001`, rerun `py scripts/merge_station.py demos/issue-10-e2e-station-demo/stations/station-e2e-001 --source-video demos/issue-10-e2e-station-demo/source-video.mp4`, then append Human Review Notes with `py scripts/review_notes.py`.
