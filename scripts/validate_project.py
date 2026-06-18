from __future__ import annotations

import json
from pathlib import Path

from validate_station_folder import validate_project_or_station


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "CONTEXT.md",
    "Makefile",
    "scripts/validate_project.py",
    "scripts/validate_station_folder.py",
    "scripts/generate_station_folder.py",
    "scripts/frame_collapse.py",
    "scripts/temporal_evidence.py",
    "scripts/validate_agent_output.py",
    "scripts/merge_station.py",
    "scripts/review_notes.py",
    "scripts/run_e2e_station_demo.py",
    ".harness/PROGRESS.md",
    ".harness/DECISIONS.md",
    ".harness/feature_list.json",
    ".harness/session_state.json",
    ".harness/quality_doc.md",
    "docs/prds/sloprail-v1-prd.md",
    "docs/prds/spec-coordinator-overlap-prd.md",
    "docs/issue-10-e2e-station-demo.md",
    "specs/sloprail/proposal.md",
    "specs/sloprail/design.md",
    "specs/sloprail/tasks.md",
    "specs/sloprail/specs/core.md",
    "specs/sloprail/out-of-scope.md",
    "specs/sloprail/open-questions.md",
    "proms/README.md",
    "proms/issue-01-product-prd.md",
    "proms/issue-02-spec-coordinator-overlap.md",
    "proms/issue-03-station-folder-validator.md",
    "proms/issue-04-source-window-manifest.md",
    "proms/issue-05-frame-collapse-report.md",
    "proms/issue-06-temporal-strip.md",
    "proms/issue-07-agent-output-validator.md",
    "proms/issue-08-normalizing-merge.md",
    "proms/issue-09-human-review-notes.md",
    "proms/issue-10-e2e-station-demo.md",
    "proms/issue-20-visual-canvas-markup.md",
    "tests/test_station_folder_validator.py",
    "tests/test_generate_station_folder.py",
    "tests/test_frame_collapse.py",
    "tests/test_temporal_evidence.py",
    "tests/test_agent_output_validator.py",
    "tests/test_merge_station.py",
    "tests/test_review_notes.py",
    "tests/test_e2e_station_demo.py",
    "tests/fixtures/station-folders/canonical-station-001/README.md",
    "tests/fixtures/station-folders/canonical-station-001/station.json",
    "tests/fixtures/station-folders/canonical-station-001/notes.md",
    "tests/fixtures/station-folders/canonical-station-001/review-notes.json",
    "tests/fixtures/station-folders/canonical-station-001/station-context/full-transcript.md",
    "tests/fixtures/station-folders/canonical-station-001/station-context/target-window-transcript.md",
    "tests/fixtures/station-folders/canonical-station-001/station-context/storyline.md",
    "tests/fixtures/station-folders/canonical-station-001/visual-evidence/source-window.mp4",
    "tests/fixtures/station-folders/canonical-station-001/visual-evidence/frame-collapse-report.json",
    "tests/fixtures/station-folders/canonical-station-001/visual-evidence/temporal-strip.png",
    "tests/fixtures/station-folders/canonical-station-001/visual-evidence/representative-frames/rep-001.jpg",
    "tests/fixtures/station-folders/canonical-station-001/visual-evidence/representative-frames/rep-002.jpg",
    "tests/fixtures/station-folders/canonical-station-001/visual-evidence/marked-frames/rep-001-marked.png",
    "tests/fixtures/station-folders/canonical-station-001/visual-evidence/marked-frames/rep-002-marked.png",
]


def require_file(path: str) -> None:
    full = ROOT / path
    if not full.is_file():
        raise SystemExit(f"Missing required file: {path}")
    if full.stat().st_size == 0:
        raise SystemExit(f"Required file is empty: {path}")


def require_json(path: str) -> None:
    full = ROOT / path
    try:
        json.loads(full.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def require_text(path: str, needle: str) -> None:
    full = ROOT / path
    text = full.read_text(encoding="utf-8")
    if needle not in text:
        raise SystemExit(f"{path} does not contain required text: {needle}")


def main() -> None:
    for path in REQUIRED_FILES:
        require_file(path)

    require_json(".harness/feature_list.json")
    require_json(".harness/session_state.json")

    require_text("CONTEXT.md", "**Station**")
    require_text("CONTEXT.md", "**Normalizing Merge**")
    require_text("CONTEXT.md", "**Human Review Notes**")
    require_text("AGENTS.md", "V1 Stations must not overlap")
    require_text("specs/sloprail/specs/core.md", "GIVEN")
    require_text("docs/prds/sloprail-v1-prd.md", "## Problem Statement")
    require_text("docs/prds/spec-coordinator-overlap-prd.md", "## Problem Statement")
    require_text("proms/README.md", "Test-driven development")
    require_text("proms/issue-03-station-folder-validator.md", "Issue #3")
    require_text("proms/issue-10-e2e-station-demo.md", "HITL")
    require_text("proms/issue-20-visual-canvas-markup.md", "Visual Canvas")
    require_text("README.md", "run_e2e_station_demo.py")
    require_text("docs/issue-10-e2e-station-demo.md", "Rerun Workflow")

    canonical_station = ROOT / "tests/fixtures/station-folders/canonical-station-001"
    station_issues = validate_project_or_station(canonical_station)
    if station_issues:
        rendered = "\n".join(
            f"{validation_issue.code}: {validation_issue.path}: {validation_issue.message}"
            for validation_issue in station_issues
        )
        raise SystemExit(f"Canonical Station Folder fixture failed validation:\n{rendered}")

    print("Sloprail project validation passed.")


if __name__ == "__main__":
    main()
