from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter, ImageStat


DEFAULT_SAMPLING_RATE_FPS = 2.0
DEFAULT_HASH_DISTANCE_THRESHOLD = 5
HASH_METHOD = "average_hash_8x8"


@dataclass(frozen=True)
class CandidateFrame:
    candidate_id: str
    path: Path
    local_time_seconds: float
    source_time_seconds: float
    perceptual_hash: str
    quality_signals: dict[str, float]
    quality_score: float


@dataclass(frozen=True)
class KeptFrame:
    representative_id: str
    candidate: CandidateFrame
    rank: int
    coverage_span: dict[str, float]
    representative_path: Path


@dataclass(frozen=True)
class RejectedFrame:
    candidate: CandidateFrame
    rejected_by: CandidateFrame
    hamming_distance: int
    reason: str


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def hamming_distance(left: str, right: str) -> int:
    if len(left) != len(right):
        raise ValueError("Perceptual hashes must be the same length.")
    return sum(1 for left_char, right_char in zip(left, right, strict=True) if left_char != right_char)


def perceptual_hash(path: Path) -> str:
    with Image.open(path) as image:
        grayscale = image.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
        pixels = list(grayscale.getdata())
    average = sum(pixels) / len(pixels)
    return "".join("1" if pixel >= average else "0" for pixel in pixels)


def quality_signals(path: Path) -> tuple[dict[str, float], float]:
    with Image.open(path) as image:
        grayscale = image.convert("L")
        stat = ImageStat.Stat(grayscale)
        brightness = float(stat.mean[0])
        contrast = float(stat.stddev[0])
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        sharpness = float(ImageStat.Stat(edges).mean[0])

    exposure_penalty = abs(brightness - 127.5) / 127.5
    signals = {
        "brightness": round(brightness, 4),
        "contrast": round(contrast, 4),
        "sharpness": round(sharpness, 4),
        "exposure_penalty": round(exposure_penalty, 4),
    }
    score = contrast + sharpness - (exposure_penalty * 10.0)
    return signals, round(score, 4)


def sample_candidate_frames(source_window: Path, candidates_dir: Path, sampling_rate_fps: float) -> list[Path]:
    candidates_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_window),
            "-vf",
            f"fps={sampling_rate_fps}",
            "-q:v",
            "2",
            str(candidates_dir / "candidate-%04d.jpg"),
        ]
    )
    return sorted(candidates_dir.glob("candidate-*.jpg"))


def build_candidates(
    frame_paths: list[Path],
    source_start_seconds: float,
    sampling_rate_fps: float,
) -> list[CandidateFrame]:
    candidates: list[CandidateFrame] = []
    for index, path in enumerate(frame_paths):
        local_time_seconds = index / sampling_rate_fps
        signals, score = quality_signals(path)
        candidates.append(
            CandidateFrame(
                candidate_id=f"candidate-{index + 1:04d}",
                path=path,
                local_time_seconds=round(local_time_seconds, 4),
                source_time_seconds=round(source_start_seconds + local_time_seconds, 4),
                perceptual_hash=perceptual_hash(path),
                quality_signals=signals,
                quality_score=score,
            )
        )
    return candidates


def choose_representative_candidates(
    candidates: list[CandidateFrame],
    hash_distance_threshold: int,
) -> tuple[list[CandidateFrame], list[RejectedFrame]]:
    kept: list[CandidateFrame] = []
    rejected: list[RejectedFrame] = []

    ranked = sorted(candidates, key=lambda item: (-item.quality_score, item.local_time_seconds, item.candidate_id))
    for candidate in ranked:
        nearest: tuple[CandidateFrame, int] | None = None
        for kept_candidate in kept:
            distance = hamming_distance(candidate.perceptual_hash, kept_candidate.perceptual_hash)
            if nearest is None or distance < nearest[1]:
                nearest = (kept_candidate, distance)

        if nearest is not None and nearest[1] <= hash_distance_threshold:
            rejected.append(
                RejectedFrame(
                    candidate=candidate,
                    rejected_by=nearest[0],
                    hamming_distance=nearest[1],
                    reason="near-duplicate-by-perceptual-hash-distance",
                )
            )
        else:
            kept.append(candidate)

    return sorted(kept, key=lambda item: item.local_time_seconds), rejected


def coverage_spans(
    kept_candidates: list[CandidateFrame],
    source_start_seconds: float,
    target_duration_seconds: float,
) -> list[dict[str, float]]:
    if not kept_candidates:
        return []

    local_times = [candidate.local_time_seconds for candidate in kept_candidates]
    spans: list[dict[str, float]] = []
    for index, local_time in enumerate(local_times):
        local_start = 0.0 if index == 0 else (local_times[index - 1] + local_time) / 2.0
        local_end = target_duration_seconds if index == len(local_times) - 1 else (local_time + local_times[index + 1]) / 2.0
        spans.append(
            {
                "station_local_start_seconds": round(local_start, 4),
                "station_local_end_seconds": round(local_end, 4),
                "source_start_seconds": round(source_start_seconds + local_start, 4),
                "source_end_seconds": round(source_start_seconds + local_end, 4),
            }
        )
    return spans


def write_kept_frames(
    kept_candidates: list[CandidateFrame],
    spans: list[dict[str, float]],
    representative_dir: Path,
) -> list[KeptFrame]:
    representative_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in representative_dir.glob("rep-*.jpg"):
        old_frame.unlink()

    kept_frames: list[KeptFrame] = []
    for index, (candidate, span) in enumerate(zip(kept_candidates, spans, strict=True), start=1):
        representative_path = representative_dir / f"rep-{index:03d}.jpg"
        shutil.copyfile(candidate.path, representative_path)
        kept_frames.append(
            KeptFrame(
                representative_id=f"rep-{index:03d}",
                candidate=candidate,
                rank=index,
                coverage_span=span,
                representative_path=representative_path,
            )
        )
    return kept_frames


def report_for(
    station_folder: Path,
    source_window: Path,
    sampling_rate_fps: float,
    hash_distance_threshold: int,
    target_duration_seconds: float,
    candidates: list[CandidateFrame],
    kept_frames: list[KeptFrame],
    rejected_frames: list[RejectedFrame],
) -> dict[str, Any]:
    rejected_by_id = {item.candidate.candidate_id: item for item in rejected_frames}
    kept_by_id = {item.candidate.candidate_id: item for item in kept_frames}

    candidate_reports: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda item: item.local_time_seconds):
        status = "kept" if candidate.candidate_id in kept_by_id else "rejected"
        candidate_report: dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "station_local_time_seconds": candidate.local_time_seconds,
            "source_time_seconds": candidate.source_time_seconds,
            "perceptual_hash": candidate.perceptual_hash,
            "quality_signals": candidate.quality_signals,
            "quality_score": candidate.quality_score,
            "status": status,
        }
        if status == "kept":
            kept = kept_by_id[candidate.candidate_id]
            candidate_report["representative_frame_id"] = kept.representative_id
            candidate_report["selection_reason"] = "highest-quality-visual-state-candidate"
        else:
            rejected = rejected_by_id[candidate.candidate_id]
            candidate_report["rejected_by_candidate_id"] = rejected.rejected_by.candidate_id
            candidate_report["hamming_distance"] = rejected.hamming_distance
            candidate_report["rejection_reason"] = rejected.reason
        candidate_reports.append(candidate_report)

    return {
        "schema_version": 1,
        "report_type": "frame-collapse-report",
        "source_window": {
            "path": relative(source_window, station_folder),
            "target_duration_seconds": round(target_duration_seconds, 4),
        },
        "sampling": {
            "frame_sampling_rate_fps": sampling_rate_fps,
            "candidate_count": len(candidates),
        },
        "perceptual_hash": {
            "method": HASH_METHOD,
            "hash_size": "8x8",
            "distance_metric": "hamming",
            "near_duplicate_threshold": hash_distance_threshold,
        },
        "representative_candidate_selection": {
            "method": "quality-ranked-temporal-frame-deduplication",
            "quality_signals": ["brightness", "contrast", "sharpness", "exposure_penalty"],
            "kept_count": len(kept_frames),
            "rejected_near_duplicate_count": len(rejected_frames),
            "manual_representative_frames": [],
        },
        "kept_frames": [
            {
                "id": kept.representative_id,
                "path": relative(kept.representative_path, station_folder),
                "source_candidate_id": kept.candidate.candidate_id,
                "station_local_time_seconds": kept.candidate.local_time_seconds,
                "source_time_seconds": kept.candidate.source_time_seconds,
                "perceptual_hash": kept.candidate.perceptual_hash,
                "quality_signals": kept.candidate.quality_signals,
                "quality_score": kept.candidate.quality_score,
                "coverage_span": kept.coverage_span,
                "selection_reason": "kept after quality ranking and perceptual-hash near-duplicate rejection",
                "selection_source": "automatic-frame-collapse",
            }
            for kept in kept_frames
        ],
        "candidates": candidate_reports,
    }


def collapse_station_frames(
    station_folder: Path,
    source_window: Path,
    source_start_seconds: float,
    target_duration_seconds: float,
    sampling_rate_fps: float = DEFAULT_SAMPLING_RATE_FPS,
    hash_distance_threshold: int = DEFAULT_HASH_DISTANCE_THRESHOLD,
) -> dict[str, Any]:
    station_folder = station_folder.resolve()
    source_window = source_window.resolve()
    visual_evidence = station_folder / "visual-evidence"
    representative_dir = visual_evidence / "representative-frames"
    report_path = visual_evidence / "frame-collapse-report.json"

    with tempfile.TemporaryDirectory(prefix="sloprail-frame-collapse-") as temp_dir:
        frame_paths = sample_candidate_frames(source_window, Path(temp_dir), sampling_rate_fps)
        if not frame_paths:
            raise RuntimeError("Frame Collapse could not sample any candidate frames from the Target Window.")
        candidates = build_candidates(frame_paths, source_start_seconds, sampling_rate_fps)
        kept_candidates, rejected_frames = choose_representative_candidates(candidates, hash_distance_threshold)
        spans = coverage_spans(kept_candidates, source_start_seconds, target_duration_seconds)
        kept_frames = write_kept_frames(kept_candidates, spans, representative_dir)
        report = report_for(
            station_folder=station_folder,
            source_window=source_window,
            sampling_rate_fps=sampling_rate_fps,
            hash_distance_threshold=hash_distance_threshold,
            target_duration_seconds=target_duration_seconds,
            candidates=candidates,
            kept_frames=kept_frames,
            rejected_frames=rejected_frames,
        )

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sloprail Frame Collapse for one Station Folder.")
    parser.add_argument("station_folder", type=Path)
    parser.add_argument("--source-window", type=Path, default=None)
    parser.add_argument("--source-start", type=float, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--sampling-rate-fps", type=float, default=DEFAULT_SAMPLING_RATE_FPS)
    parser.add_argument("--hash-distance-threshold", type=int, default=DEFAULT_HASH_DISTANCE_THRESHOLD)
    args = parser.parse_args()

    source_window = args.source_window or args.station_folder / "visual-evidence" / "source-window.mp4"
    report = collapse_station_frames(
        station_folder=args.station_folder,
        source_window=source_window,
        source_start_seconds=args.source_start,
        target_duration_seconds=args.duration,
        sampling_rate_fps=args.sampling_rate_fps,
        hash_distance_threshold=args.hash_distance_threshold,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
