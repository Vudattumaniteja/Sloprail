from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_CATEGORIES = {"fps", "visual", "general"}
ALLOWED_REVIEW_SUBJECTS = {"replacement_render", "merged_output"}
TIME_TOLERANCE_SECONDS = 0.001


class ReviewNotesError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReviewNote:
    id: str
    review_subject: str
    station_local_time_seconds: float
    source_video_time_seconds: float
    category: str
    observation: str
    normalization_report_reference: dict[str, str] | None = None


def load_json(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReviewNotesError(f"Required JSON file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewNotesError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ReviewNotesError(f"JSON file must contain an object: {path}")
    return parsed


def as_float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ReviewNotesError(f"{label} must be a number.")
    return float(value)


def target_window(station: dict[str, Any]) -> dict[str, float]:
    target = station.get("target_window")
    if not isinstance(target, dict):
        raise ReviewNotesError("station.json must contain target_window.")
    source_start = as_float(target.get("source_start_seconds"), "target_window.source_start_seconds")
    source_end = as_float(target.get("source_end_seconds"), "target_window.source_end_seconds")
    duration = target.get("duration_seconds")
    duration_seconds = as_float(duration, "target_window.duration_seconds") if duration is not None else source_end - source_start
    if source_start < 0 or source_end <= source_start or duration_seconds <= 0:
        raise ReviewNotesError("Target Window timing is invalid.")
    if abs((source_end - source_start) - duration_seconds) > TIME_TOLERANCE_SECONDS:
        raise ReviewNotesError("Target Window duration must match end minus start.")
    return {
        "source_start_seconds": source_start,
        "source_end_seconds": source_end,
        "duration_seconds": duration_seconds,
    }


def default_review_notes(station: dict[str, Any]) -> dict[str, Any]:
    target = target_window(station)
    return {
        "schema_version": 1,
        "station_id": station.get("station_id"),
        "target_window": {
            "source_start_seconds": target["source_start_seconds"],
            "source_end_seconds": target["source_end_seconds"],
            "duration_seconds": target["duration_seconds"],
        },
        "workflow": {
            "auto_fix": False,
            "visible_normalization_damage": "record_in_human_review_notes_and_rerun_manually",
        },
        "allowed_categories": sorted(ALLOWED_CATEGORIES),
        "notes": [],
    }


def review_notes_path(station_folder: Path) -> Path:
    station = load_json(station_folder / "station.json")
    review = station.get("human_review_notes")
    if isinstance(review, dict) and isinstance(review.get("path"), str) and review["path"].strip():
        configured = Path(review["path"])
        if configured.is_absolute():
            raise ReviewNotesError("human_review_notes.path must be Station Folder relative.")
        resolved = (station_folder / configured).resolve()
        try:
            resolved.relative_to(station_folder.resolve())
        except ValueError as exc:
            raise ReviewNotesError("human_review_notes.path must stay inside the Station Folder.") from exc
        return resolved
    return station_folder / "review-notes.json"


def load_or_create_review_notes(station_folder: Path) -> dict[str, Any]:
    path = review_notes_path(station_folder)
    if path.is_file():
        return load_json(path)
    station = load_json(station_folder / "station.json")
    return default_review_notes(station)


def next_note_id(notes: list[Any]) -> str:
    return f"review-note-{len(notes) + 1:03d}"


def build_review_note(
    station_folder: Path,
    review_subject: str,
    station_local_time_seconds: float,
    category: str,
    observation: str,
    normalization_report_path: str | None = None,
    normalization_report_detail: str | None = None,
) -> ReviewNote:
    station = load_json(station_folder / "station.json")
    target = target_window(station)
    if review_subject not in ALLOWED_REVIEW_SUBJECTS:
        allowed = ", ".join(sorted(ALLOWED_REVIEW_SUBJECTS))
        raise ReviewNotesError(f"review_subject must be one of: {allowed}.")
    if category not in ALLOWED_CATEGORIES:
        allowed = ", ".join(sorted(ALLOWED_CATEGORIES))
        raise ReviewNotesError(f"category must be one of: {allowed}.")
    if station_local_time_seconds < 0 or station_local_time_seconds > target["duration_seconds"]:
        raise ReviewNotesError("station_local_time_seconds must fall inside the Target Window.")
    if not observation.strip():
        raise ReviewNotesError("observation must not be empty.")

    existing = load_or_create_review_notes(station_folder)
    notes = existing.get("notes")
    if not isinstance(notes, list):
        notes = []
    reference = None
    if normalization_report_path is not None or normalization_report_detail is not None:
        if not normalization_report_path or not normalization_report_detail:
            raise ReviewNotesError("Normalization Report references require both path and detail.")
        reference = {
            "path": normalization_report_path,
            "detail": normalization_report_detail,
        }

    return ReviewNote(
        id=next_note_id(notes),
        review_subject=review_subject,
        station_local_time_seconds=station_local_time_seconds,
        source_video_time_seconds=target["source_start_seconds"] + station_local_time_seconds,
        category=category,
        observation=observation.strip(),
        normalization_report_reference=reference,
    )


def note_to_dict(note: ReviewNote) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": note.id,
        "review_subject": note.review_subject,
        "station_local_time_seconds": round(note.station_local_time_seconds, 3),
        "source_video_time_seconds": round(note.source_video_time_seconds, 3),
        "category": note.category,
        "observation": note.observation,
    }
    if note.normalization_report_reference is not None:
        payload["normalization_report_reference"] = note.normalization_report_reference
    return payload


def write_human_review_note(
    station_folder: Path,
    review_subject: str,
    station_local_time_seconds: float,
    category: str,
    observation: str,
    normalization_report_path: str | None = None,
    normalization_report_detail: str | None = None,
) -> Path:
    station_folder = station_folder.resolve()
    station = load_json(station_folder / "station.json")
    review_path = review_notes_path(station_folder)
    review_notes = load_or_create_review_notes(station_folder)
    if review_notes.get("schema_version") is None:
        review_notes["schema_version"] = 1
    if "workflow" not in review_notes:
        review_notes["workflow"] = default_review_notes(station)["workflow"]
    if "allowed_categories" not in review_notes:
        review_notes["allowed_categories"] = sorted(ALLOWED_CATEGORIES)
    if "target_window" not in review_notes:
        review_notes["target_window"] = default_review_notes(station)["target_window"]
    notes = review_notes.setdefault("notes", [])
    if not isinstance(notes, list):
        raise ReviewNotesError("review-notes.json notes must be a list.")

    note = build_review_note(
        station_folder=station_folder,
        review_subject=review_subject,
        station_local_time_seconds=station_local_time_seconds,
        category=category,
        observation=observation,
        normalization_report_path=normalization_report_path,
        normalization_report_detail=normalization_report_detail,
    )
    notes.append(note_to_dict(note))
    review_path.write_text(json.dumps(review_notes, indent=2), encoding="utf-8")
    return review_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write one Sloprail Human Review Note for a Station.")
    parser.add_argument("station_folder", type=Path)
    parser.add_argument("--review-subject", choices=sorted(ALLOWED_REVIEW_SUBJECTS), required=True)
    parser.add_argument("--station-local-time", type=float, required=True)
    parser.add_argument("--category", choices=sorted(ALLOWED_CATEGORIES), required=True)
    parser.add_argument("--observation", required=True)
    parser.add_argument("--normalization-report-path")
    parser.add_argument("--normalization-report-detail")
    args = parser.parse_args()

    try:
        path = write_human_review_note(
            station_folder=args.station_folder,
            review_subject=args.review_subject,
            station_local_time_seconds=args.station_local_time,
            category=args.category,
            observation=args.observation,
            normalization_report_path=args.normalization_report_path,
            normalization_report_detail=args.normalization_report_detail,
        )
    except ReviewNotesError as exc:
        raise SystemExit(f"Human Review Notes update failed: {exc}") from exc
    print(f"Wrote Human Review Notes: {path}")


if __name__ == "__main__":
    main()
