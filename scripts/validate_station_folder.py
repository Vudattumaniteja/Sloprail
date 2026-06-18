from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


REQUIRED_STATION_FILES = [
    "README.md",
    "station.json",
    "notes.md",
]

REQUIRED_STATION_DIRS = [
    "visual-evidence",
    "station-context",
]

REQUIRED_STATION_CONTEXT = [
    "full-transcript.md",
    "target-window-transcript.md",
    "storyline.md",
    "design-rules.md",
]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class StationRecord:
    folder: Path
    station_id: str
    source_video_id: str
    source_video_path: str
    start_seconds: float
    end_seconds: float


def load_json(path: Path, issues: list[ValidationIssue]) -> dict[str, Any] | None:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        issues.append(issue("missing_file", path, "Required file is missing."))
        return None
    except json.JSONDecodeError as exc:
        issues.append(issue("invalid_json", path, f"JSON is invalid: {exc}"))
        return None
    if not isinstance(parsed, dict):
        issues.append(issue("invalid_json", path, "station.json must contain a JSON object."))
        return None
    return parsed


def issue(code: str, path: Path, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path=path.as_posix(), message=message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def resolve_relative(folder: Path, relative_path: str) -> Path:
    return (folder / relative_path).resolve()


def validate_image_file(path: Path, issues: list[ValidationIssue], expected_format: str | None = None) -> None:
    try:
        with Image.open(path) as image:
            image.verify()
            if expected_format is not None and image.format != expected_format:
                issues.append(issue("invalid_image_format", path, f"Image must be {expected_format}, got {image.format}."))
    except FileNotFoundError:
        issues.append(issue("unresolved_path_reference", path, "Image path does not resolve."))
    except Exception as exc:
        issues.append(issue("invalid_image_file", path, f"Image file is not readable: {exc}"))


def validate_required_files(folder: Path, issues: list[ValidationIssue]) -> None:
    for relative in REQUIRED_STATION_FILES:
        path = folder / relative
        if not path.is_file():
            issues.append(issue("missing_file", path, f"Required Station Folder file is missing: {relative}"))
        elif path.stat().st_size == 0:
            issues.append(issue("empty_file", path, f"Required Station Folder file is empty: {relative}"))

    for relative in REQUIRED_STATION_DIRS:
        path = folder / relative
        if not path.is_dir():
            issues.append(issue("missing_directory", path, f"Required Station Folder directory is missing: {relative}"))


def validate_notes(folder: Path, issues: list[ValidationIssue]) -> None:
    notes_path = folder / "notes.md"
    if not notes_path.is_file():
        return
    text = read_text(notes_path).strip()
    if not text:
        issues.append(issue("empty_station_level_note", notes_path, "notes.md must contain a Station-Level Note."))


def validate_no_html(folder: Path, issues: list[ValidationIssue]) -> None:
    for path in folder.rglob("*.html"):
        issues.append(issue("html_preview_out_of_scope", path, "V1 Station Folders must not include an HTML preview contract."))


def collect_path_references(station: dict[str, Any]) -> list[str]:
    references: list[str] = []

    def walk(value: Any, parent_key: str | None = None) -> None:
        if parent_key == "agent_output":
            return
        if isinstance(value, dict):
            for key, nested in value.items():
                is_path_key = key in {"path", "file", "relative_path"} or key.endswith("_path")
                if is_path_key and isinstance(nested, str):
                    references.append(nested)
                else:
                    walk(nested, key)
        elif isinstance(value, list):
            for nested in value:
                walk(nested, parent_key)

    walk(station)
    return references


def validate_path_references(folder: Path, station: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for reference in collect_path_references(station):
        if Path(reference).is_absolute():
            issues.append(issue("absolute_path_reference", folder / "station.json", f"Path reference must be Station Folder relative: {reference}"))
            continue
        resolved = resolve_relative(folder, reference)
        try:
            resolved.relative_to(folder.resolve())
        except ValueError:
            issues.append(issue("path_reference_escapes_station_folder", folder / "station.json", f"Path reference escapes the Station Folder: {reference}"))
            continue
        if not resolved.exists():
            issues.append(issue("unresolved_path_reference", folder / "station.json", f"station.json path reference does not resolve: {reference}"))


def validate_partial_station_context(folder: Path, station: dict[str, Any], issues: list[ValidationIssue]) -> None:
    readme_path = folder / "README.md"
    readme = read_text(readme_path) if readme_path.is_file() else ""

    context = station.get("station_context")
    if not isinstance(context, dict):
        issues.append(issue("missing_station_context", folder / "station.json", "station.json must declare station_context."))
        return

    partial = context.get("partial")
    missing = context.get("missing")
    files = context.get("files")

    if missing is None:
        missing = []
    if not isinstance(missing, list) or not all(isinstance(item, str) for item in missing):
        issues.append(issue("invalid_partial_station_context", folder / "station.json", "station_context.missing must be a list of filenames."))
        return

    if files is None:
        files = []
    if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
        issues.append(issue("invalid_station_context_files", folder / "station.json", "station_context.files must be a list of filenames."))
        return

    declared_files = set(files)
    declared_missing = set(missing)
    absent_required = {
        required
        for required in REQUIRED_STATION_CONTEXT
        if not (folder / "station-context" / required).is_file()
    }

    undeclared_absent = absent_required - declared_missing
    if undeclared_absent:
        issues.append(
            issue(
                "missing_station_context_file",
                folder / "station-context",
                "Missing Station Context files must be explicitly declared as Partial Station Context: "
                + ", ".join(sorted(undeclared_absent)),
            )
        )

    for relative in declared_files:
        if not (folder / relative).is_file():
            issues.append(issue("unresolved_station_context_file", folder / "station.json", f"Declared Station Context file is missing: {relative}"))

    if declared_missing:
        readme_declares_partial = "Partial Station Context" in readme
        readme_declares_missing = all(item in readme for item in declared_missing)
        if partial is not True:
            issues.append(issue("partial_context_not_flagged", folder / "station.json", "station_context.partial must be true when context is missing."))
        if not readme_declares_partial or not readme_declares_missing:
            issues.append(
                issue(
                    "partial_context_not_declared_in_readme",
                    readme_path,
                    "README.md must declare Partial Station Context and name each missing context file.",
                )
            )
    elif partial is True:
        issues.append(issue("partial_context_without_missing_files", folder / "station.json", "station_context.partial is true but no missing context is declared."))


def validate_frame_collapse_report(folder: Path, station: dict[str, Any], issues: list[ValidationIssue]) -> None:
    visual_evidence = station.get("visual_evidence")
    if not isinstance(visual_evidence, dict):
        issues.append(issue("missing_visual_evidence", folder / "station.json", "station.json must declare visual_evidence."))
        return

    report_ref = visual_evidence.get("frame_collapse_report")
    if not isinstance(report_ref, dict) or not isinstance(report_ref.get("path"), str):
        issues.append(issue("missing_frame_collapse_report", folder / "station.json", "station.json must reference visual-evidence/frame-collapse-report.json."))
        return

    report_path = resolve_relative(folder, report_ref["path"])
    report = load_json(report_path, issues)
    if report is None:
        return

    sampling = report.get("sampling")
    perceptual_hash = report.get("perceptual_hash")
    selection = report.get("representative_candidate_selection")
    kept_frames = report.get("kept_frames")
    candidates = report.get("candidates")
    if not isinstance(sampling, dict):
        issues.append(issue("invalid_frame_collapse_report", report_path, "Frame Collapse Report must contain sampling."))
        return
    if not isinstance(perceptual_hash, dict):
        issues.append(issue("invalid_frame_collapse_report", report_path, "Frame Collapse Report must contain perceptual_hash."))
        return
    if not isinstance(selection, dict):
        issues.append(issue("invalid_frame_collapse_report", report_path, "Frame Collapse Report must contain representative_candidate_selection."))
        return
    if not isinstance(kept_frames, list):
        issues.append(issue("invalid_frame_collapse_report", report_path, "Frame Collapse Report kept_frames must be a list."))
        return
    if not isinstance(candidates, list):
        issues.append(issue("invalid_frame_collapse_report", report_path, "Frame Collapse Report candidates must be a list."))
        return

    if sampling.get("frame_sampling_rate_fps") != 2.0:
        issues.append(issue("invalid_frame_sampling_rate", report_path, "Frame Collapse must use the v1 Frame Sampling Rate of 2 fps."))
    if sampling.get("candidate_count") != len(candidates):
        issues.append(issue("invalid_frame_collapse_counts", report_path, "sampling.candidate_count must match candidates length."))
    if perceptual_hash.get("distance_metric") != "hamming":
        issues.append(issue("invalid_perceptual_hash_contract", report_path, "Frame Collapse must use Hamming distance for perceptual-hash comparison."))
    if not isinstance(perceptual_hash.get("near_duplicate_threshold"), int):
        issues.append(issue("invalid_perceptual_hash_contract", report_path, "perceptual_hash.near_duplicate_threshold must be an integer."))

    manual_frames = selection.get("manual_representative_frames")
    if not isinstance(manual_frames, list):
        issues.append(issue("missing_manual_representative_frame_support", report_path, "Frame Collapse Report must represent Manual Representative Frame support."))
    if selection.get("kept_count") != len(kept_frames):
        issues.append(issue("invalid_frame_collapse_counts", report_path, "representative_candidate_selection.kept_count must match kept_frames length."))
    rejected_count = sum(1 for candidate in candidates if isinstance(candidate, dict) and candidate.get("status") == "rejected")
    if selection.get("rejected_near_duplicate_count") != rejected_count:
        issues.append(
            issue(
                "invalid_frame_collapse_counts",
                report_path,
                "representative_candidate_selection.rejected_near_duplicate_count must match rejected candidate count.",
            )
        )

    for kept in kept_frames:
        if not isinstance(kept, dict):
            issues.append(issue("invalid_frame_collapse_report", report_path, "Each kept frame must be a JSON object."))
            continue
        kept_path = kept.get("path")
        if not isinstance(kept_path, str):
            issues.append(issue("invalid_frame_collapse_report", report_path, "Each kept frame must declare path."))
            continue
        if not resolve_relative(folder, kept_path).is_file():
            issues.append(issue("unresolved_path_reference", report_path, f"Frame Collapse kept frame path does not resolve: {kept_path}"))
        if not isinstance(kept.get("coverage_span"), dict):
            issues.append(issue("invalid_frame_collapse_report", report_path, "Each kept frame must declare a Coverage Span."))
        elif not isinstance(kept["coverage_span"].get("id"), str):
            issues.append(issue("invalid_frame_collapse_report", report_path, "Each Coverage Span must declare an id."))


def validate_visual_evidence_contract(folder: Path, station: dict[str, Any], issues: list[ValidationIssue]) -> None:
    visual_evidence = station.get("visual_evidence")
    if not isinstance(visual_evidence, dict):
        return

    temporal_strip = visual_evidence.get("temporal_strip")
    representative_frames = visual_evidence.get("representative_frames")
    marked_frames = visual_evidence.get("marked_frames")
    if not isinstance(temporal_strip, dict) or temporal_strip.get("path") != "visual-evidence/temporal-strip.png":
        issues.append(issue("missing_temporal_strip", folder / "station.json", "station.json must reference visual-evidence/temporal-strip.png."))
    else:
        validate_image_file(resolve_relative(folder, temporal_strip["path"]), issues, expected_format="PNG")
    if not isinstance(representative_frames, list) or not representative_frames:
        issues.append(issue("missing_representative_frames", folder / "station.json", "visual_evidence.representative_frames must be a non-empty list."))
        representative_frames = []
    if not isinstance(marked_frames, list) or not marked_frames:
        issues.append(issue("missing_marked_frames", folder / "station.json", "visual_evidence.marked_frames must be a non-empty list."))
        marked_frames = []

    marked_by_id = {
        frame.get("id"): frame
        for frame in marked_frames
        if isinstance(frame, dict) and isinstance(frame.get("id"), str)
    }
    for frame in representative_frames:
        if not isinstance(frame, dict):
            issues.append(issue("invalid_representative_frame", folder / "station.json", "Each Representative Frame entry must be a JSON object."))
            continue
        frame_id = frame.get("id")
        frame_path = frame.get("path")
        coverage_span = frame.get("coverage_span")
        marked_frame_id = frame.get("marked_frame_id")
        if not isinstance(frame_id, str):
            issues.append(issue("invalid_representative_frame", folder / "station.json", "Each Representative Frame must declare id."))
        if not isinstance(frame_path, str) or not resolve_relative(folder, frame_path).is_file():
            issues.append(issue("unresolved_path_reference", folder / "station.json", f"Representative Frame path does not resolve: {frame_path}"))
        else:
            validate_image_file(resolve_relative(folder, frame_path), issues)
        if not isinstance(coverage_span, dict) or not isinstance(coverage_span.get("id"), str):
            issues.append(issue("invalid_coverage_span", folder / "station.json", "Each Representative Frame must link a Coverage Span with id and timing."))
            continue
        required_span_numbers = [
            coverage_span.get("source_start_seconds"),
            coverage_span.get("source_end_seconds"),
            coverage_span.get("station_local_start_seconds"),
            coverage_span.get("station_local_end_seconds"),
        ]
        if any(as_float(value) is None for value in required_span_numbers):
            issues.append(issue("invalid_coverage_span", folder / "station.json", "Coverage Span timing must include source and station-local start/end seconds."))
        if not isinstance(marked_frame_id, str) or marked_frame_id not in marked_by_id:
            issues.append(issue("missing_marked_frame_link", folder / "station.json", "Each Representative Frame must link its Marked Frame."))
            continue
        marked = marked_by_id[marked_frame_id]
        if marked.get("representative_frame_id") != frame_id:
            issues.append(issue("invalid_marked_frame_link", folder / "station.json", "Marked Frame representative_frame_id must match its Representative Frame."))
        if marked.get("coverage_span_id") != coverage_span.get("id"):
            issues.append(issue("invalid_marked_frame_link", folder / "station.json", "Marked Frame coverage_span_id must match its Representative Frame Coverage Span."))

    for frame in marked_frames:
        if not isinstance(frame, dict):
            issues.append(issue("invalid_marked_frame", folder / "station.json", "Each Marked Frame entry must be a JSON object."))
            continue
        frame_path = frame.get("path")
        if not isinstance(frame_path, str) or not resolve_relative(folder, frame_path).is_file():
            issues.append(issue("unresolved_path_reference", folder / "station.json", f"Marked Frame path does not resolve: {frame_path}"))
        else:
            validate_image_file(resolve_relative(folder, frame_path), issues, expected_format="PNG")
        markup_status = frame.get("markup_status")
        if markup_status not in {"no_visual_markup", "visual_markup_present"}:
            issues.append(issue("invalid_markup_status", folder / "station.json", "Marked Frames must declare markup_status as no_visual_markup or visual_markup_present."))


def station_record_from_json(folder: Path, station: dict[str, Any], issues: list[ValidationIssue]) -> StationRecord | None:
    station_id = station.get("station_id")
    if not isinstance(station_id, str) or not station_id.strip():
        issues.append(issue("missing_station_id", folder / "station.json", "station.json must contain station_id."))
        station_id = folder.name

    source_video = station.get("source_video")
    if not isinstance(source_video, dict):
        issues.append(issue("missing_source_video", folder / "station.json", "station.json must contain source_video."))
        return None
    source_video_id = source_video.get("id")
    source_video_path = source_video.get("path")
    if not isinstance(source_video_id, str) or not source_video_id.strip():
        issues.append(issue("missing_source_video_id", folder / "station.json", "source_video.id is required."))
        return None
    if not isinstance(source_video_path, str) or not source_video_path.strip():
        issues.append(issue("missing_source_video_path", folder / "station.json", "source_video.path is required."))
        return None

    target_window = station.get("target_window")
    if not isinstance(target_window, dict):
        issues.append(issue("missing_target_window", folder / "station.json", "station.json must contain target_window."))
        return None
    start_seconds = as_float(target_window.get("source_start_seconds"))
    end_seconds = as_float(target_window.get("source_end_seconds"))
    duration_seconds = as_float(target_window.get("duration_seconds"))
    if start_seconds is None or end_seconds is None:
        issues.append(issue("invalid_target_window_timing", folder / "station.json", "Target Window start and end seconds must be numbers."))
        return None
    if start_seconds < 0:
        issues.append(issue("invalid_target_window_timing", folder / "station.json", "Target Window start must be non-negative."))
    if end_seconds <= start_seconds:
        issues.append(issue("invalid_target_window_timing", folder / "station.json", "Target Window end must be greater than start."))
    if duration_seconds is not None and abs((end_seconds - start_seconds) - duration_seconds) > 0.001:
        issues.append(issue("invalid_target_window_timing", folder / "station.json", "Target Window duration must match end minus start."))

    return StationRecord(
        folder=folder,
        station_id=station_id,
        source_video_id=source_video_id,
        source_video_path=source_video_path,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
    )


def validate_station_folder(folder: Path) -> tuple[StationRecord | None, list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    folder = folder.resolve()

    validate_required_files(folder, issues)
    validate_notes(folder, issues)
    validate_no_html(folder, issues)

    station = load_json(folder / "station.json", issues)
    if station is None:
        return None, issues

    validate_path_references(folder, station, issues)
    validate_partial_station_context(folder, station, issues)
    validate_frame_collapse_report(folder, station, issues)
    validate_visual_evidence_contract(folder, station, issues)
    record = station_record_from_json(folder, station, issues)
    return record, issues


def find_station_folders(path: Path) -> list[Path]:
    if (path / "station.json").is_file():
        return [path]
    return sorted({station_json.parent for station_json in path.rglob("station.json")})


def validate_project_or_station(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    folders = find_station_folders(path.resolve())
    if not folders:
        return [issue("no_station_folders", path, "No Station Folders with station.json were found.")]

    records: list[StationRecord] = []
    for folder in folders:
        record, station_issues = validate_station_folder(folder)
        issues.extend(station_issues)
        if record is not None:
            records.append(record)

    source_videos = {(record.source_video_id, record.source_video_path) for record in records}
    if len(source_videos) > 1:
        issues.append(issue("multiple_source_videos", path, "V1 projects must contain exactly one Source Video."))

    for index, current in enumerate(records):
        for other in records[index + 1 :]:
            overlaps = current.start_seconds < other.end_seconds and other.start_seconds < current.end_seconds
            if overlaps:
                issues.append(
                    issue(
                        "overlapping_station_target_windows",
                        other.folder / "station.json",
                        f"Station {other.station_id} overlaps {current.station_id}; V1 Stations must not overlap in source time.",
                    )
                )

    return issues


def issues_to_report(path: Path, issues: list[ValidationIssue]) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "valid": not issues,
        "issue_count": len(issues),
        "issues": [issue.__dict__ for issue in issues],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Sloprail Station Folder handoff contracts.")
    parser.add_argument("path", type=Path, help="Station Folder path or a project folder containing Station Folders.")
    parser.add_argument("--json", action="store_true", help="Print a JSON validation report.")
    args = parser.parse_args()

    issues = validate_project_or_station(args.path)
    report = issues_to_report(args.path, issues)

    if args.json:
        print(json.dumps(report, indent=2))
    elif issues:
        for validation_issue in issues:
            print(f"{validation_issue.code}: {validation_issue.path}: {validation_issue.message}")
    else:
        print("Station Handoff Validation passed.")

    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
