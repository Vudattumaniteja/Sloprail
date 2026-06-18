from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

try:
    from generate_station_folder import StationRequest, generate_station_folder
    from merge_station import merge_station
    from review_notes import write_human_review_note
    from validate_agent_output import result_to_report, validate_agent_output
    from validate_station_folder import issues_to_report, validate_project_or_station
except ModuleNotFoundError:
    from scripts.generate_station_folder import StationRequest, generate_station_folder
    from scripts.merge_station import merge_station
    from scripts.review_notes import write_human_review_note
    from scripts.validate_agent_output import result_to_report, validate_agent_output
    from scripts.validate_station_folder import issues_to_report, validate_project_or_station


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "demos" / "issue-10-e2e-station-demo"
STATION_ID = "station-e2e-001"
SOURCE_VIDEO_ID = "fixture-source-video-001"
TARGET_START_SECONDS = 1.0
TARGET_END_SECONDS = 3.0


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def relative_to_root(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def require_media_tools() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise RuntimeError(f"Missing required media tool(s): {', '.join(missing)}")


def reset_output_root(output_root: Path, force: bool) -> None:
    output_root = output_root.resolve()
    try:
        output_root.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Demo output root must stay inside the repository: {output_root}") from exc

    if output_root.exists():
        if not force:
            raise RuntimeError(f"Demo output already exists: {output_root}. Re-run with --force to replace it.")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def make_fixture_source_video(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=30:duration=5",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=5",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(path),
        ]
    )


def make_replacement_render(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    duration = TARGET_END_SECONDS - TARGET_START_SECONDS
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size=160x90:rate=15:duration={duration}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv444p",
            "-movflags",
            "+faststart",
            str(path),
        ]
    )


def write_context_file(context_root: Path, filename: str, body: str) -> Path:
    context_root.mkdir(parents=True, exist_ok=True)
    path = context_root / filename
    path.write_text(body.strip() + "\n", encoding="utf-8")
    return path


def write_context_files(output_root: Path) -> dict[str, Path]:
    context_root = output_root / "source-context"
    return {
        "full_transcript": write_context_file(
            context_root,
            "full-transcript.md",
            """
            # Full Source Video Transcript

            0.000s-5.000s: Fixture color-pattern Source Video used to prove the Sloprail Station workflow mechanically.
            """,
        ),
        "target_window_transcript": write_context_file(
            context_root,
            "target-window-transcript.md",
            """
            # Target Window Transcript

            1.000s-3.000s: Replace the visual pattern while preserving the original Source Video audio during merge.
            """,
        ),
        "storyline": write_context_file(
            context_root,
            "storyline.md",
            """
            # Storyline

            This fixture demonstrates a single Station moving from Source Video evidence to Replacement Render and Merged Output.
            """,
        ),
        "design_rules": write_context_file(
            context_root,
            "design-rules.md",
            """
            # Design Rules

            Use a visibly different Replacement Render so the Target Window replacement can be inspected without subjective ambiguity.
            """,
        ),
    }


def write_completed_agent_output(station_folder: Path) -> None:
    output_json = {
        "schema_version": 1,
        "station_id": STATION_ID,
        "source_video_id": SOURCE_VIDEO_ID,
        "status": "completed",
        "replacement_render_path": "agent-output/replacement-render.mp4",
        "render_notes_path": "agent-output/render-notes.md",
    }
    (station_folder / "agent-output" / "output.json").write_text(json.dumps(output_json, indent=2), encoding="utf-8")
    (station_folder / "agent-output" / "render-notes.md").write_text(
        "\n".join(
            [
                "# Agent Render Notes",
                "",
                "Simulated Agent Action for the fixture-backed demo.",
                "The Replacement Render intentionally uses a lower resolution, lower frame rate, and yuv444p pixel format so Normalizing Merge evidence is inspectable.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def fail_if_issues(label: str, report: dict[str, Any]) -> None:
    if report.get("issue_count") != 0:
        raise RuntimeError(f"{label} failed:\n{json.dumps(report, indent=2)}")


def run_demo(output_root: Path, force: bool) -> dict[str, Any]:
    require_media_tools()
    reset_output_root(output_root, force=force)

    source_video = output_root / "source-video.mp4"
    station_folder = output_root / "stations" / STATION_ID
    make_fixture_source_video(source_video)
    context = write_context_files(output_root)

    generate_station_folder(
        StationRequest(
            source_video=source_video,
            output_folder=station_folder,
            station_id=STATION_ID,
            source_video_id=SOURCE_VIDEO_ID,
            source_start_seconds=TARGET_START_SECONDS,
            source_end_seconds=TARGET_END_SECONDS,
            station_level_note="Replace the Target Window visual pattern with a clear alternate fixture render while preserving Source Video audio.",
            full_transcript=context["full_transcript"],
            target_window_transcript=context["target_window_transcript"],
            storyline=context["storyline"],
            design_rules=context["design_rules"],
        )
    )
    station_handoff_report = issues_to_report(station_folder, validate_project_or_station(station_folder))
    fail_if_issues("Station Handoff Validation", station_handoff_report)

    replacement_render = station_folder / "agent-output" / "replacement-render.mp4"
    make_replacement_render(replacement_render)
    write_completed_agent_output(station_folder)
    agent_output_report = result_to_report(validate_agent_output(station_folder))
    fail_if_issues("Agent Output Validation", agent_output_report)
    if not agent_output_report.get("merge_allowed"):
        raise RuntimeError("Agent Output Validation passed but did not allow merge.")

    merge_report = merge_station(station_folder, source_video=source_video)
    normalization_report_path = Path(merge_report["normalization"]["normalization_report_path"])

    write_human_review_note(
        station_folder=station_folder,
        review_subject="replacement_render",
        station_local_time_seconds=0.5,
        category="visual",
        observation="Fixture Replacement Render is intentionally synthetic and visibly different from the Source Video; acceptable for mechanical demo only.",
    )
    write_human_review_note(
        station_folder=station_folder,
        review_subject="merged_output",
        station_local_time_seconds=1.0,
        category="fps",
        observation="Merged Output preserved playback continuity; normalization changed Replacement Render frame rate to match the Source Video.",
        normalization_report_path=relative_to_root(normalization_report_path),
        normalization_report_detail="Frame rate, resolution, and pixel format normalization were expected in this fixture demo.",
    )
    final_station_report = issues_to_report(station_folder, validate_project_or_station(station_folder))
    fail_if_issues("Final Station Handoff Validation", final_station_report)

    demo_report = {
        "schema_version": 1,
        "status": "completed",
        "issue": "https://github.com/Vudattumaniteja/Sloprail/issues/10",
        "output_root": relative_to_root(output_root),
        "source_video": relative_to_root(source_video),
        "station_folder": relative_to_root(station_folder),
        "station_handoff_validation": station_handoff_report,
        "agent_output_validation": agent_output_report,
        "merge_report": merge_report,
        "final_station_handoff_validation": final_station_report,
        "human_review_notes": relative_to_root(station_folder / "review-notes.json"),
        "key_outputs": {
            "source_window": relative_to_root(station_folder / "visual-evidence" / "source-window.mp4"),
            "frame_collapse_report": relative_to_root(station_folder / "visual-evidence" / "frame-collapse-report.json"),
            "temporal_strip": relative_to_root(station_folder / "visual-evidence" / "temporal-strip.png"),
            "replacement_render": relative_to_root(replacement_render),
            "merged_output": relative_to_root(Path(merge_report["merged_output"]["path"])),
            "merge_report": relative_to_root(station_folder / "merge-output" / "merge-report.json"),
            "normalization_report": relative_to_root(normalization_report_path),
        },
        "manual_review_observations": [
            "Replacement Render is synthetic fixture media, so visual acceptability is limited to mechanical inspectability.",
            "Normalization changes are expected and recorded as HITL evidence, not auto-fixed.",
        ],
    }
    report_path = output_root / "demo-report.json"
    report_path.write_text(json.dumps(demo_report, indent=2), encoding="utf-8")
    return demo_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the fixture-backed Sloprail V1 end-to-end Station demo.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--force", action="store_true", help="Replace an existing demo output directory.")
    args = parser.parse_args()

    try:
        report = run_demo(args.output_root, force=args.force)
    except (RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise SystemExit(f"End-to-end Station demo failed: {exc}") from exc
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
