from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from validate_agent_output import DURATION_TOLERANCE_SECONDS, validate_agent_output
except ModuleNotFoundError:
    from scripts.validate_agent_output import DURATION_TOLERANCE_SECONDS, validate_agent_output


class MergeError(RuntimeError):
    pass


@dataclass(frozen=True)
class TargetWindow:
    source_start_seconds: float
    source_end_seconds: float
    duration_seconds: float


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def require_media_tools() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise MergeError(f"Missing required media tool(s): {', '.join(missing)}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MergeError(f"Required JSON file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MergeError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise MergeError(f"JSON file must contain an object: {path}")
    return parsed


def as_float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise MergeError(f"{label} must be a number.")
    return float(value)


def parse_frame_rate(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        try:
            denominator_float = float(denominator)
            if denominator_float == 0:
                return None
            return float(numerator) / denominator_float
        except ValueError:
            return None
    try:
        return float(value)
    except ValueError:
        return None


def ffmpeg_rate(value: Any) -> str:
    if isinstance(value, str) and value and value != "0/0":
        return value
    return "30"


def resolve_station_path(station_folder: Path, relative_path: str, source: Path) -> Path:
    candidate = Path(relative_path)
    resolved = candidate if candidate.is_absolute() else (station_folder / candidate)
    resolved = resolved.resolve()
    if candidate.is_absolute():
        return resolved
    try:
        resolved.relative_to(station_folder.resolve())
    except ValueError as exc:
        raise MergeError(f"Path reference escapes the Station Folder in {source}: {relative_path}") from exc
    return resolved


def probe_media(path: Path) -> dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)

    properties: dict[str, Any] = {
        "duration_seconds": float(data.get("format", {}).get("duration", 0.0)),
        "width": video.get("width"),
        "height": video.get("height"),
        "frame_rate": video.get("avg_frame_rate"),
        "video_codec": video.get("codec_name"),
        "pixel_format": video.get("pix_fmt"),
        "audio_present": audio is not None,
    }
    if audio is not None:
        properties["audio_codec"] = audio.get("codec_name")
    return properties


def target_window_from_station(station: dict[str, Any]) -> TargetWindow:
    target = station.get("target_window")
    if not isinstance(target, dict):
        raise MergeError("station.json must contain target_window.")
    start = as_float(target.get("source_start_seconds"), "target_window.source_start_seconds")
    end = as_float(target.get("source_end_seconds"), "target_window.source_end_seconds")
    duration = target.get("duration_seconds")
    duration_seconds = as_float(duration, "target_window.duration_seconds") if duration is not None else end - start
    if start < 0 or end <= start or duration_seconds <= 0:
        raise MergeError("Target Window timing is invalid.")
    if abs((end - start) - duration_seconds) > 0.001:
        raise MergeError("Target Window duration must match end minus start.")
    return TargetWindow(start, end, duration_seconds)


def replacement_render_path(station_folder: Path, station: dict[str, Any]) -> Path:
    agent_output = load_json(station_folder / "agent-output" / "output.json")
    value = agent_output.get("replacement_render_path")
    if not isinstance(value, str) or not value.strip():
        configured = station.get("agent_output")
        value = configured.get("replacement_render_path") if isinstance(configured, dict) else None
    if not isinstance(value, str) or not value.strip():
        value = "agent-output/replacement-render.mp4"
    path = resolve_station_path(station_folder, value, station_folder / "agent-output" / "output.json")
    if not path.is_file():
        raise MergeError(f"Replacement Render is missing: {path}")
    return path


def source_video_path(station_folder: Path, station: dict[str, Any], override: Path | None) -> Path:
    if override is not None:
        path = override.resolve()
    else:
        source_video = station.get("source_video")
        if not isinstance(source_video, dict) or not isinstance(source_video.get("path"), str):
            raise MergeError("station.json must contain source_video.path or --source-video must be provided.")
        path = resolve_station_path(station_folder, source_video["path"], station_folder / "station.json")
    if not path.is_file():
        raise MergeError(f"Source Video is missing: {path}")
    return path


def detect_normalization_changes(source: dict[str, Any], replacement: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    comparisons = [
        ("resolution", f"{replacement.get('width')}x{replacement.get('height')}", f"{source.get('width')}x{source.get('height')}"),
        ("pixel_format", replacement.get("pixel_format"), "yuv420p"),
        ("video_codec", replacement.get("video_codec"), "h264"),
    ]
    source_fps = parse_frame_rate(source.get("frame_rate"))
    replacement_fps = parse_frame_rate(replacement.get("frame_rate"))
    comparisons.append(("frame_rate", replacement.get("frame_rate"), source.get("frame_rate")))

    for field, before, after in comparisons:
        if field == "frame_rate" and source_fps is not None and replacement_fps is not None:
            changed = abs(source_fps - replacement_fps) > 0.001
        else:
            changed = before != after
        if changed:
            changes.append({"field": field, "from": before, "to": after})
    return changes


def normalize_replacement(
    replacement: Path,
    normalized: Path,
    source_properties: dict[str, Any],
) -> None:
    width = source_properties.get("width")
    height = source_properties.get("height")
    if not isinstance(width, int) or not isinstance(height, int):
        raise MergeError("Source Video width and height could not be measured.")
    rate = ffmpeg_rate(source_properties.get("frame_rate"))
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(replacement),
            "-an",
            "-vf",
            f"scale={width}:{height},fps={rate},format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            str(normalized),
        ]
    )


def merge_with_ffmpeg(
    source_video: Path,
    normalized_replacement: Path,
    output_path: Path,
    target_window: TargetWindow,
    source_properties: dict[str, Any],
) -> None:
    audio_present = bool(source_properties.get("audio_present"))
    if audio_present:
        filter_complex = (
            f"[0:v]trim=start=0:end={target_window.source_start_seconds},setpts=PTS-STARTPTS[v0];"
            f"[0:a]atrim=start=0:end={target_window.source_start_seconds},asetpts=PTS-STARTPTS[a0];"
            "[1:v]setpts=PTS-STARTPTS[v1];"
            f"[0:a]atrim=start={target_window.source_start_seconds}:end={target_window.source_end_seconds},asetpts=PTS-STARTPTS[a1];"
            f"[0:v]trim=start={target_window.source_end_seconds},setpts=PTS-STARTPTS[v2];"
            f"[0:a]atrim=start={target_window.source_end_seconds},asetpts=PTS-STARTPTS[a2];"
            "[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]"
        )
        map_args = ["-map", "[v]", "-map", "[a]", "-c:a", "aac"]
    else:
        filter_complex = (
            f"[0:v]trim=start=0:end={target_window.source_start_seconds},setpts=PTS-STARTPTS[v0];"
            "[1:v]setpts=PTS-STARTPTS[v1];"
            f"[0:v]trim=start={target_window.source_end_seconds},setpts=PTS-STARTPTS[v2];"
            "[v0][v1][v2]concat=n=3:v=1:a=0[v]"
        )
        map_args = ["-map", "[v]"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_video),
            "-i",
            str(normalized_replacement),
            "-filter_complex",
            filter_complex,
            *map_args,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )


def write_normalization_report(path: Path, changes: list[dict[str, Any]], output_path: Path) -> None:
    if changes:
        lines = ["# Normalization Report", "", "## Changes"]
        for change in changes:
            lines.append(f"- {change['field']}: `{change['from']}` -> `{change['to']}`")
    else:
        lines = ["# Normalization Report", "", "No ffmpeg normalization changes were required."]
    lines.extend(["", "## Output", f"- Normalized Replacement Render: `{output_path.as_posix()}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_duration(replacement_properties: dict[str, Any], target_window: TargetWindow) -> None:
    actual = replacement_properties.get("duration_seconds")
    if not isinstance(actual, int | float):
        raise MergeError("Replacement Render duration could not be measured.")
    if abs(float(actual) - target_window.duration_seconds) > DURATION_TOLERANCE_SECONDS:
        raise MergeError(
            f"Replacement Render duration {float(actual):.3f}s must match Target Window "
            f"{target_window.duration_seconds:.3f}s within +/-0.05s."
        )


def merge_station(station_folder: Path, source_video: Path | None = None, output_dir: Path | None = None) -> dict[str, Any]:
    require_media_tools()
    station_folder = station_folder.resolve()
    station = load_json(station_folder / "station.json")
    target_window = target_window_from_station(station)
    source = source_video_path(station_folder, station, source_video)
    replacement = replacement_render_path(station_folder, station)

    validation = validate_agent_output(station_folder)
    if not validation.merge_allowed:
        rendered = "\n".join(f"{item.code}: {item.path}: {item.message}" for item in validation.issues)
        raise MergeError(f"Agent Output Validation failed; Station is not eligible for merge.\n{rendered}")

    source_properties = probe_media(source)
    replacement_properties = validation.replacement_render_media_properties or probe_media(replacement)
    validate_duration(replacement_properties, target_window)

    merge_dir = (output_dir.resolve() if output_dir is not None else station_folder / "merge-output")
    normalized_path = merge_dir / "normalized-replacement-render.mp4"
    merged_output_path = merge_dir / "merged-output.mp4"
    report_path = merge_dir / "merge-report.json"
    normalization_report_path = merge_dir / "normalization-report.md"
    merge_dir.mkdir(parents=True, exist_ok=True)

    normalization_changes = detect_normalization_changes(source_properties, replacement_properties)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_normalized = Path(temp_dir) / "normalized-replacement-render.mp4"
        normalize_replacement(replacement, temp_normalized, source_properties)
        shutil.copy2(temp_normalized, normalized_path)
        merge_with_ffmpeg(source, temp_normalized, merged_output_path, target_window, source_properties)

    merged_properties = probe_media(merged_output_path)
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "completed",
        "station_id": station.get("station_id"),
        "source_video": {
            "id": station.get("source_video", {}).get("id") if isinstance(station.get("source_video"), dict) else None,
            "path": source.as_posix(),
            "media_properties": source_properties,
        },
        "target_window": {
            "source_start_seconds": target_window.source_start_seconds,
            "source_end_seconds": target_window.source_end_seconds,
            "duration_seconds": target_window.duration_seconds,
        },
        "replacement_render": {
            "path": replacement.as_posix(),
            "media_properties": replacement_properties,
            "duration_delta_seconds": float(replacement_properties["duration_seconds"]) - target_window.duration_seconds,
        },
        "normalization": {
            "changes": normalization_changes,
            "normalized_replacement_render_path": normalized_path.as_posix(),
            "normalization_report_path": normalization_report_path.as_posix(),
        },
        "merged_output": {
            "path": merged_output_path.as_posix(),
            "media_properties": merged_properties,
            "original_audio_preserved": bool(source_properties.get("audio_present")) == bool(merged_properties.get("audio_present")),
        },
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_normalization_report(normalization_report_path, normalization_changes, normalized_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge one completed Sloprail Station with ffmpeg Normalizing Merge.")
    parser.add_argument("station_folder", type=Path, help="Station Folder containing a completed agent-output package.")
    parser.add_argument("--source-video", type=Path, help="Full Source Video to receive the Replacement Render.")
    parser.add_argument("--output-dir", type=Path, help="Directory for Merged Output and merge evidence. Defaults to station/merge-output.")
    args = parser.parse_args()

    try:
        report = merge_station(args.station_folder, source_video=args.source_video, output_dir=args.output_dir)
    except (MergeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Normalizing Merge failed: {exc}") from exc
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
