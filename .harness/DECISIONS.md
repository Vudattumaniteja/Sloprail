# Design Decisions

## 2026-06-18: Initial harness setup
- Decision: Initialize Sloprail as a docs-first repo with harness files before app implementation.
- Reason: The project has a rich domain contract and should not start with feature code before the Station Folder and merge contracts are stable.
- Constraints: Use `CONTEXT.md` vocabulary and keep v1 non-HTML, evidence-only, and agent-handoff focused.

## 2026-06-18: V1 Station boundary
- Decision: A Station is one non-overlapping Target Window from one Source Video.
- Reason: This keeps agent work independently runnable and avoids overlap merge conflicts.
- Constraints: Future overlap support remains experimental, not v1.

## 2026-06-18: V1 merge boundary
- Decision: Agents produce Replacement Renders; ffmpeg automation performs the merge.
- Reason: Video replacement is deterministic infrastructure work and should not be delegated to LLM agents.
- Constraints: Original audio is preserved, duration tolerance is +/-0.05s, and normalization must be reported.
