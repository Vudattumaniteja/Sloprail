from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {"completed", "blocked", "failed"}
DURATION_TOLERANCE_SECONDS = 0.05


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class AgentOutputValidationResult:
    station_folder: str
    status: str | None
    merge_allowed: bool
    replacement_render_media_properties: dict[str, Any] | None
    issues: list[ValidationIssue]


def issue(code: str, path: Path, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path=path.as_posix(), message=message)


def load_json(path: Path, label: str, issues: list[ValidationIssue]) -> dict[str, Any] | None:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        issues.append(issue(f"missing_{label}", path, f"Required {label.replace('_', ' ')} is missing."))
        return None
    except json.JSONDecodeError as exc:
        issues.append(issue("invalid_json", path, f"JSON is invalid: {exc}"))
        return None
    if not isinstance(parsed, dict):
        issues.append(issue("invalid_json", path, f"{path.name} must contain a JSON object."))
        return None
    return parsed


def as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def resolve_station_path(station_folder: Path, relative_path: str, issues: list[ValidationIssue], source: Path) -> Path | None:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        issues.append(issue("absolute_path_reference", source, f"Path reference must be Station Folder relative: {relative_path}"))
        return None
    resolved = (station_folder / candidate).resolve()
    try:
        resolved.relative_to(station_folder.resolve())
    except ValueError:
        issues.append(issue("path_reference_escapes_station_folder", source, f"Path reference escapes the Station Folder: {relative_path}"))
        return None
    return resolved


def probe_media(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)

    media_properties: dict[str, Any] = {
        "duration_seconds": float(data.get("format", {}).get("duration", 0.0)),
        "width": video.get("width"),
        "height": video.get("height"),
        "frame_rate": video.get("avg_frame_rate"),
        "video_codec": video.get("codec_name"),
        "pixel_format": video.get("pix_fmt"),
        "audio_present": audio is not None,
    }
    if audio is not None:
        media_properties["audio_codec"] = audio.get("codec_name")
    return media_properties


def station_identity(station: dict[str, Any], station_json_path: Path, issues: list[ValidationIssue]) -> tuple[str | None, str | None, float | None]:
    station_id = station.get("station_id")
    if not isinstance(station_id, str) or not station_id.strip():
        issues.append(issue("missing_station_id", station_json_path, "station.json must contain station_id."))
        station_id = None

    source_video = station.get("source_video")
    source_video_id = None
    if not isinstance(source_video, dict) or not isinstance(source_video.get("id"), str):
        issues.append(issue("missing_source_video_id", station_json_path, "station.json must contain source_video.id."))
    else:
        source_video_id = source_video["id"]

    target_window = station.get("target_window")
    duration_seconds = None
    if not isinstance(target_window, dict):
        issues.append(issue("missing_target_window", station_json_path, "station.json must contain target_window."))
    else:
        duration_seconds = as_float(target_window.get("duration_seconds"))
        if duration_seconds is None:
            start = as_float(target_window.get("source_start_seconds"))
            end = as_float(target_window.get("source_end_seconds"))
            if start is not None and end is not None:
                duration_seconds = end - start
        if duration_seconds is None or duration_seconds <= 0:
            issues.append(issue("invalid_target_window_duration", station_json_path, "Target Window duration must be a positive number."))

    return station_id, source_video_id, duration_seconds


def output_path(output: dict[str, Any], station: dict[str, Any], key: str, fallback: str) -> str:
    value = output.get(key)
    if isinstance(value, str) and value.strip():
        return value
    agent_output = station.get("agent_output")
    if isinstance(agent_output, dict):
        station_value = agent_output.get(key)
        if isinstance(station_value, str) and station_value.strip():
            return station_value
    return fallback


def validate_optional_source_directories(
    station_folder: Path,
    output: dict[str, Any],
    output_json_path: Path,
    issues: list[ValidationIssue],
) -> None:
    source_directories = output.get("source_directories")
    if source_directories is None:
        return
    if not isinstance(source_directories, list) or not all(isinstance(item, str) for item in source_directories):
        issues.append(issue("invalid_source_directories", output_json_path, "source_directories must be a list of Station Folder relative paths."))
        return
    for relative in source_directories:
        resolved = resolve_station_path(station_folder, relative, issues, output_json_path)
        if resolved is not None and not resolved.is_dir():
            issues.append(issue("missing_source_directory", output_json_path, f"Optional source directory does not resolve: {relative}"))


def validate_declared_output_paths(
    station_folder: Path,
    output: dict[str, Any],
    output_json_path: Path,
    issues: list[ValidationIssue],
) -> None:
    for key in ("replacement_render_path", "render_notes_path"):
        value = output.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            issues.append(issue("invalid_output_path", output_json_path, f"{key} must be a non-empty Station Folder relative path when declared."))
            continue
        resolve_station_path(station_folder, value, issues, output_json_path)


def validate_agent_output(station_folder: Path) -> AgentOutputValidationResult:
    station_folder = station_folder.resolve()
    issues: list[ValidationIssue] = []
    station_json_path = station_folder / "station.json"
    station = load_json(station_json_path, "station_json", issues)
    if station is None:
        return AgentOutputValidationResult(station_folder.as_posix(), None, False, None, issues)

    expected_station_id, expected_source_video_id, target_duration_seconds = station_identity(station, station_json_path, issues)
    output_json_path = station_folder / "agent-output" / "output.json"
    output = load_json(output_json_path, "output_json", issues)
    if output is None:
        return AgentOutputValidationResult(station_folder.as_posix(), None, False, None, issues)

    status = output.get("status")
    if output.get("schema_version") != 1:
        issues.append(issue("invalid_output_schema_version", output_json_path, "output.json schema_version must be 1."))

    if not isinstance(status, str) or status not in ALLOWED_STATUSES:
        issues.append(issue("invalid_agent_output_status", output_json_path, "status must be one of completed, blocked, or failed."))
        status = None

    output_station_id = output.get("station_id")
    if not isinstance(output_station_id, str) or not output_station_id.strip():
        issues.append(issue("missing_output_station_id", output_json_path, "output.json must declare station_id."))
    elif expected_station_id is not None and output_station_id != expected_station_id:
        issues.append(issue("station_id_mismatch", output_json_path, "output.json station_id must match station.json station_id."))

    output_source_video_id = output.get("source_video_id")
    if not isinstance(output_source_video_id, str) or not output_source_video_id.strip():
        issues.append(issue("missing_output_source_video_id", output_json_path, "output.json must declare source_video_id."))
    elif expected_source_video_id is not None and output_source_video_id != expected_source_video_id:
        issues.append(issue("source_video_id_mismatch", output_json_path, "output.json source_video_id must match station.json source_video.id."))

    validate_optional_source_directories(station_folder, output, output_json_path, issues)
    validate_declared_output_paths(station_folder, output, output_json_path, issues)

    replacement_render_media_properties: dict[str, Any] | None = None
    replacement_render_ref = None
    replacement_render_path = None
    if status == "completed" or "replacement_render_path" in output:
        replacement_render_ref = output_path(output, station, "replacement_render_path", "agent-output/replacement-render.mp4")
        replacement_render_path = resolve_station_path(station_folder, replacement_render_ref, issues, output_json_path)
        if replacement_render_path is not None and replacement_render_path.is_file():
            try:
                replacement_render_media_properties = probe_media(replacement_render_path)
            except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as exc:
                issues.append(issue("invalid_replacement_render_media", replacement_render_path, f"Replacement Render Media Properties could not be probed: {exc}"))

    if status == "completed":
        render_notes_ref = output_path(output, station, "render_notes_path", "agent-output/render-notes.md")
        render_notes_path = resolve_station_path(station_folder, render_notes_ref, issues, output_json_path)

        if replacement_render_path is not None:
            if not replacement_render_path.is_file():
                issues.append(issue("missing_replacement_render", replacement_render_path, "Completed Agent Action must include replacement-render.mp4."))

        if render_notes_path is not None:
            if not render_notes_path.is_file():
                issues.append(issue("missing_agent_render_notes", render_notes_path, "Completed Agent Action must include Agent Render Notes."))
            elif not render_notes_path.read_text(encoding="utf-8").strip():
                issues.append(issue("empty_agent_render_notes", render_notes_path, "Agent Render Notes must not be empty."))

        if replacement_render_media_properties is not None and target_duration_seconds is not None:
            actual_duration = as_float(replacement_render_media_properties.get("duration_seconds"))
            if actual_duration is None:
                issues.append(issue("missing_replacement_render_duration", replacement_render_path or output_json_path, "Replacement Render duration could not be measured."))
            elif abs(actual_duration - target_duration_seconds) > DURATION_TOLERANCE_SECONDS:
                issues.append(
                    issue(
                        "replacement_render_duration_mismatch",
                        replacement_render_path or output_json_path,
                        f"Replacement Render duration {actual_duration:.3f}s must match Target Window {target_duration_seconds:.3f}s within +/-0.05s.",
                    )
                )

    merge_allowed = status == "completed" and not issues
    return AgentOutputValidationResult(
        station_folder=station_folder.as_posix(),
        status=status,
        merge_allowed=merge_allowed,
        replacement_render_media_properties=replacement_render_media_properties,
        issues=issues,
    )


def result_to_report(result: AgentOutputValidationResult) -> dict[str, Any]:
    return {
        "station_folder": result.station_folder,
        "status": result.status,
        "merge_allowed": result.merge_allowed,
        "replacement_render_media_properties": result.replacement_render_media_properties,
        "issue_count": len(result.issues),
        "issues": [validation_issue.__dict__ for validation_issue in result.issues],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Sloprail Agent Action return package before merge.")
    parser.add_argument("station_folder", type=Path, help="Station Folder containing agent-output/output.json.")
    parser.add_argument("--json", action="store_true", help="Print a JSON validation report.")
    args = parser.parse_args()

    result = validate_agent_output(args.station_folder)
    if args.json:
        print(json.dumps(result_to_report(result), indent=2))
    elif result.issues:
        for validation_issue in result.issues:
            print(f"{validation_issue.code}: {validation_issue.path}: {validation_issue.message}")
    elif result.merge_allowed:
        print("Agent Output Validation passed. Station is eligible for merge.")
    else:
        print(f"Agent Output Validation passed. Station is not mergeable because status={result.status}.")

    if result.issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
