from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "CONTEXT.md",
    "Makefile",
    ".harness/PROGRESS.md",
    ".harness/DECISIONS.md",
    ".harness/feature_list.json",
    ".harness/session_state.json",
    ".harness/quality_doc.md",
    "docs/prds/sloprail-v1-prd.md",
    "docs/prds/spec-coordinator-overlap-prd.md",
    "specs/sloprail/proposal.md",
    "specs/sloprail/design.md",
    "specs/sloprail/tasks.md",
    "specs/sloprail/specs/core.md",
    "specs/sloprail/out-of-scope.md",
    "specs/sloprail/open-questions.md",
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
    require_text("AGENTS.md", "V1 Stations must not overlap")
    require_text("specs/sloprail/specs/core.md", "GIVEN")
    require_text("docs/prds/sloprail-v1-prd.md", "## Problem Statement")
    require_text("docs/prds/spec-coordinator-overlap-prd.md", "## Problem Statement")

    print("Sloprail project validation passed.")


if __name__ == "__main__":
    main()
