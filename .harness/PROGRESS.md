# Project Progress

## Current State
- Project name: Sloprail
- Repo type: docs-first product/spec harness
- Test status: `py scripts/validate_project.py` validates required files and contract text; `make check` is available where GNU Make exists
- GitHub: private repository at `https://github.com/Vudattumaniteja/Sloprail`

## Completed
- [x] Domain glossary captured in `CONTEXT.md`
- [x] V1 product boundary resolved
- [x] Two PRD tracks created
- [x] OpenSpec-compatible bundle created
- [x] Harness initialized

## In Progress
- [x] Push private GitHub repository
- [x] Publish PRD issues

## Known Issues
- No application code exists yet.
- The existing local `prototype-station-001/` folder is intentionally excluded from the v1 repo contract because it includes an HTML preview artifact.

## GitHub Issues
- [#1 PRD: Sloprail V1 Station Folder and Replacement Render Workflow](https://github.com/Vudattumaniteja/Sloprail/issues/1)
- [#2 PRD: Sloprail and spec-coordinator overlap boundary](https://github.com/Vudattumaniteja/Sloprail/issues/2)
- [#3 Build canonical non-HTML Station Folder fixture and validator](https://github.com/Vudattumaniteja/Sloprail/issues/3)
- [#4 Generate source-window media and Station README manifest](https://github.com/Vudattumaniteja/Sloprail/issues/4)
- [#5 Implement perceptual-hash Frame Collapse report](https://github.com/Vudattumaniteja/Sloprail/issues/5)
- [#6 Render Representative Frames, Marked Frames, and Temporal Strip](https://github.com/Vudattumaniteja/Sloprail/issues/6)
- [#7 Validate agent-output contract before merge](https://github.com/Vudattumaniteja/Sloprail/issues/7)
- [#8 Merge one completed Station with ffmpeg Normalizing Merge](https://github.com/Vudattumaniteja/Sloprail/issues/8)
- [#9 Add Human Review Notes for merged playback](https://github.com/Vudattumaniteja/Sloprail/issues/9)
- [#10 Run first fixture-backed end-to-end Station demo](https://github.com/Vudattumaniteja/Sloprail/issues/10)

## Next Steps
1. Build a minimal Station Folder generator.
2. Build frame sampling and perceptual-hash reduction.
3. Build ffmpeg merge automation with Normalization Report.
