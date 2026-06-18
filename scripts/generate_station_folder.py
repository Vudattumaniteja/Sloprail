from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from validate_station_folder import validate_project_or_station
except ModuleNotFoundError:
    from scripts.validate_station_folder import validate_project_or_station


REQUIRED_CONTEXT_FILES = {
    "full_transcript": "full-transcript.md",
    "target_window_transcript": "target-window-transcript.md",
    "storyline": "storyline.md",
    "design_rules": "design-rules.md",
}


@dataclass(frozen=True)
class StationRequest:
    source_video: Path
    output_folder: Path
    station_id: str
    source_video_id: str
    source_start_seconds: float
    source_end_seconds: float
    station_level_note: str
    full_transcript: Path | None = None
    target_window_transcript: Path | None = None
    storyline: Path | None = None
    design_rules: Path | None = None


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def format_seconds(value: float) -> str:
    return f"{value:.3f}s"


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_optional(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.read_text(encoding="utf-8")


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

    media_properties: dict[str, Any] = {
        "duration_seconds": float(data.get("format", {}).get("duration", 0.0)),
        "width": video.get("width"),
        "height": video.get("height"),
        "frame_rate": video.get("avg_frame_rate"),
        "video_codec": video.get("codec_name"),
        "audio_present": audio is not None,
    }
    if audio is not None:
        media_properties["audio_codec"] = audio.get("codec_name")
    return media_properties


def extract_source_window(source_video: Path, output_path: Path, start_seconds: float, duration_seconds: float) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(start_seconds),
            "-i",
            str(source_video),
            "-t",
            str(duration_seconds),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )


def write_context_files(request: StationRequest) -> tuple[list[str], list[str]]:
    station_context = request.output_folder / "station-context"
    station_context.mkdir(parents=True, exist_ok=True)

    files: list[str] = []
    missing: list[str] = []
    for field_name, filename in REQUIRED_CONTEXT_FILES.items():
        source = getattr(request, field_name)
        target = station_context / filename
        text = read_optional(source)
        if text is None:
            missing.append(filename)
        else:
            target.write_text(text, encoding="utf-8")
            files.append(relative(target, request.output_folder))
    return files, missing


def write_readme(request: StationRequest, duration_seconds: float, missing_context: list[str]) -> None:
    partial_section = ""
    if missing_context:
        missing = ", ".join(f"`{name}`" for name in missing_context)
        partial_section = (
            "\n## Partial Station Context\n"
            f"This Station intentionally omits {missing}. Do not invent missing Station Context; ask the human if the Replacement Render depends on it.\n"
        )

    readme = f"""# Station {request.station_id}

## First Read
This Station Folder is an Agent Work Packet for one Target Window from one Source Video. Inspect `station.json`, `notes.md`, `station-context/`, and `visual-evidence/source-window.mp4` before planning work. The Read Boundary is this Station Folder unless the human explicitly expands context.

## Target Window
- Source Video: `{request.source_video_id}`
- Source time: `{format_seconds(request.source_start_seconds)}` to `{format_seconds(request.source_end_seconds)}`
- Station-local time: `0.000s` to `{format_seconds(duration_seconds)}`
- Station-local duration: `{format_seconds(duration_seconds)}`
{partial_section}
## Required Output
Write Agent Action results under `agent-output/`.
"""
    (request.output_folder / "README.md").write_text(readme, encoding="utf-8")


def build_station_json(
    request: StationRequest,
    source_window_path: Path,
    context_files: list[str],
    missing_context: list[str],
    media_properties: dict[str, Any],
) -> dict[str, Any]:
    duration_seconds = request.source_end_seconds - request.source_start_seconds
    return {
        "schema_version": 1,
        "station_id": request.station_id,
        "source_video": {
            "id": request.source_video_id,
            "path": relative(source_window_path, request.output_folder),
            "source_filename": request.source_video.name,
        },
        "target_window": {
            "source_start_seconds": request.source_start_seconds,
            "source_end_seconds": request.source_end_seconds,
            "duration_seconds": duration_seconds,
            "station_local_start_seconds": 0.0,
            "station_local_end_seconds": duration_seconds,
        },
        "read_boundary": {
            "scope": "station-folder-only",
            "instruction": "Agent Actions should read only this Station Folder unless the human explicitly expands context.",
        },
        "media_properties": {
            "source_window": media_properties,
        },
        "station_context": {
            "partial": bool(missing_context),
            "files": context_files,
            "missing": missing_context,
        },
        "visual_evidence": {
            "source_window": {
                "path": relative(source_window_path, request.output_folder),
            }
        },
        "agent_output": {
            "directory": "agent-output",
            "replacement_render_path": "agent-output/replacement-render.mp4",
            "render_notes_path": "agent-output/render-notes.md",
            "output_json_path": "agent-output/output.json",
        },
    }


def generate_station_folder(request: StationRequest) -> Path:
    if request.source_end_seconds <= request.source_start_seconds:
        raise ValueError("Target Window end must be greater than start.")
    if not request.station_level_note.strip():
        raise ValueError("A Station-Level Note is required before handoff.")

    request.output_folder.mkdir(parents=True, exist_ok=True)
    (request.output_folder / "visual-evidence").mkdir(exist_ok=True)
    (request.output_folder / "agent-output").mkdir(exist_ok=True)
    (request.output_folder / "notes.md").write_text(request.station_level_note.strip() + "\n", encoding="utf-8")

    duration_seconds = request.source_end_seconds - request.source_start_seconds
    source_window_path = request.output_folder / "visual-evidence" / "source-window.mp4"
    extract_source_window(request.source_video, source_window_path, request.source_start_seconds, duration_seconds)
    media_properties = probe_media(source_window_path)

    context_files, missing_context = write_context_files(request)
    write_readme(request, duration_seconds, missing_context)
    station = build_station_json(request, source_window_path, context_files, missing_context, media_properties)
    (request.output_folder / "station.json").write_text(json.dumps(station, indent=2), encoding="utf-8")

    issues = validate_project_or_station(request.output_folder)
    if issues:
        rendered = "\n".join(f"{item.code}: {item.path}: {item.message}" for item in issues)
        raise RuntimeError(f"Generated Station Folder failed Station Handoff Validation:\n{rendered}")

    return request.output_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Sloprail Station Folder shell from one Source Video Target Window.")
    parser.add_argument("--source-video", type=Path, required=True)
    parser.add_argument("--output-folder", type=Path, required=True)
    parser.add_argument("--station-id", required=True)
    parser.add_argument("--source-video-id", required=True)
    parser.add_argument("--start", type=float, required=True, dest="source_start_seconds")
    parser.add_argument("--end", type=float, required=True, dest="source_end_seconds")
    parser.add_argument("--note", required=True, dest="station_level_note")
    parser.add_argument("--full-transcript", type=Path)
    parser.add_argument("--target-window-transcript", type=Path)
    parser.add_argument("--storyline", type=Path)
    parser.add_argument("--design-rules", type=Path)
    args = parser.parse_args()

    folder = generate_station_folder(StationRequest(**vars(args)))
    print(f"Generated Station Folder: {folder}")


if __name__ == "__main__":
    main()
