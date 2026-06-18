from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


MARKUP_STATUS_NONE = "no_visual_markup"
MARKUP_STATUS_PRESENT = "visual_markup_present"


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def format_seconds(value: float) -> str:
    return f"{value:.3f}s"


def span_duration(span: dict[str, Any]) -> float:
    return float(span["station_local_end_seconds"]) - float(span["station_local_start_seconds"])


def timing_label(frame: dict[str, Any]) -> str:
    span = frame["coverage_span"]
    span_id = span["id"]
    source_start = format_seconds(float(span["source_start_seconds"]))
    source_end = format_seconds(float(span["source_end_seconds"]))
    local_start = format_seconds(float(span["station_local_start_seconds"]))
    local_end = format_seconds(float(span["station_local_end_seconds"]))
    duration = format_seconds(span_duration(span))
    return f"{span_id} | source {source_start}-{source_end} | local {local_start}-{local_end} | dur {duration}"


def write_marked_frames(
    station_folder: Path,
    kept_frames: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    marked_dir = station_folder / "visual-evidence" / "marked-frames"
    marked_dir.mkdir(parents=True, exist_ok=True)

    marked_frames: list[dict[str, Any]] = []
    for frame in kept_frames:
        representative_path = station_folder / frame["path"]
        marked_path = marked_dir / f"{frame['id']}-marked.png"
        markup_status = MARKUP_STATUS_PRESENT
        if not marked_path.is_file():
            with Image.open(representative_path) as image:
                image.convert("RGB").save(marked_path)
            markup_status = MARKUP_STATUS_NONE
        marked_frames.append(
            {
                "id": f"{frame['id']}-marked",
                "representative_frame_id": frame["id"],
                "coverage_span_id": frame["coverage_span"]["id"],
                "path": relative(marked_path, station_folder),
                "markup_status": markup_status,
            }
        )
    return marked_frames


def render_temporal_strip(
    station_folder: Path,
    kept_frames: list[dict[str, Any]],
    marked_frames: list[dict[str, Any]],
) -> dict[str, Any]:
    visual_evidence = station_folder / "visual-evidence"
    strip_path = visual_evidence / "temporal-strip.png"
    visual_evidence.mkdir(parents=True, exist_ok=True)

    card_width = 320
    image_height = 180
    label_height = 74
    padding = 16
    gap = 12
    width = padding * 2 + (card_width * len(marked_frames)) + (gap * max(len(marked_frames) - 1, 0))
    height = padding * 2 + image_height + label_height
    strip = Image.new("RGB", (max(width, 1), height), "white")
    draw = ImageDraw.Draw(strip)
    font = ImageFont.load_default()

    marked_by_representative = {frame["representative_frame_id"]: frame for frame in marked_frames}
    labels: list[dict[str, str]] = []
    for index, frame in enumerate(kept_frames):
        marked = marked_by_representative[frame["id"]]
        x = padding + index * (card_width + gap)
        y = padding
        with Image.open(station_folder / marked["path"]) as image:
            thumbnail = ImageOps.contain(image.convert("RGB"), (card_width, image_height))
            image_x = x + (card_width - thumbnail.width) // 2
            image_y = y + (image_height - thumbnail.height) // 2
            strip.paste(thumbnail, (image_x, image_y))

        draw.rectangle([x, y, x + card_width, y + image_height], outline="#222222", width=2)
        label = timing_label(frame)
        label_y = y + image_height + 10
        draw.multiline_text((x, label_y), label, fill="#111111", font=font, spacing=4)
        labels.append({"coverage_span_id": frame["coverage_span"]["id"], "label": label})

    strip.save(strip_path)
    return {
        "path": relative(strip_path, station_folder),
        "embedded_timing_labels": labels,
    }


def build_temporal_evidence(station_folder: Path, kept_frames: list[dict[str, Any]]) -> dict[str, Any]:
    station_folder = station_folder.resolve()
    marked_frames = write_marked_frames(station_folder, kept_frames)
    temporal_strip = render_temporal_strip(station_folder, kept_frames, marked_frames)
    return {
        "temporal_strip": temporal_strip,
        "marked_frames": marked_frames,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Sloprail Marked Frames and Temporal Strip evidence.")
    parser.add_argument("station_folder", type=Path)
    parser.add_argument("--frame-collapse-report", type=Path, default=None)
    args = parser.parse_args()

    station_folder = args.station_folder.resolve()
    report_path = args.frame_collapse_report or station_folder / "visual-evidence" / "frame-collapse-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    evidence = build_temporal_evidence(station_folder, report["kept_frames"])
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
