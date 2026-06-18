from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.merge_station import MergeError, merge_station, probe_media


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "tests" / "fixtures" / "station-folders" / "canonical-station-001"


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def write_station_json(station: Path, source_video: Path) -> None:
    payload = json.loads((station / "station.json").read_text(encoding="utf-8"))
    payload["source_video"]["path"] = source_video.as_posix()
    payload["target_window"] = {
        "source_start_seconds": 1.0,
        "source_end_seconds": 3.0,
        "duration_seconds": 2.0,
    }
    (station / "station.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_completed_output(station: Path) -> None:
    payload = {
        "schema_version": 1,
        "station_id": "station-001",
        "source_video_id": "source-video-001",
        "status": "completed",
    }
    (station / "agent-output" / "output.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (station / "agent-output" / "render-notes.md").write_text("Agent Render Notes for the Replacement Render.\n", encoding="utf-8")


def make_source_video(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=320x180:rate=30:duration=4",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=4",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def make_replacement_render(path: Path, duration: float = 2.0) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size=160x90:rate=15:duration={duration}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv444p",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


@unittest.skipUnless(has_ffmpeg(), "ffmpeg and ffprobe are required for Normalizing Merge tests")
class MergeStationTests(unittest.TestCase):
    def copy_station(self, temp_dir: str) -> Path:
        station = Path(temp_dir) / "station"
        shutil.copytree(CANONICAL, station)
        return station

    def prepare_mergeable_station(self, temp_dir: str, replacement_duration: float = 2.0) -> tuple[Path, Path]:
        station = self.copy_station(temp_dir)
        source_video = Path(temp_dir) / "source-video.mp4"
        make_source_video(source_video)
        write_station_json(station, source_video)
        write_completed_output(station)
        make_replacement_render(station / "agent-output" / "replacement-render.mp4", replacement_duration)
        return station, source_video

    def test_merges_one_completed_station_and_preserves_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station, source_video = self.prepare_mergeable_station(temp_dir)

            report = merge_station(station, source_video=source_video)
            output_path = Path(report["merged_output"]["path"])

            self.assertEqual(report["status"], "completed")
            self.assertTrue(output_path.is_file())
            self.assertTrue((station / "merge-output" / "merge-report.json").is_file())
            self.assertTrue((station / "merge-output" / "normalization-report.md").is_file())

            output_properties = probe_media(output_path)
            self.assertTrue(output_properties["audio_present"])
            self.assertAlmostEqual(output_properties["duration_seconds"], 4.0, delta=0.15)
            self.assertEqual(output_properties["width"], 320)
            self.assertEqual(output_properties["height"], 180)

            normalization_report = (station / "merge-output" / "normalization-report.md").read_text(encoding="utf-8")
            self.assertIn("resolution", normalization_report)
            self.assertIn("frame_rate", normalization_report)
            self.assertIn("pixel_format", normalization_report)

    def test_rejects_duration_mismatch_before_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station, source_video = self.prepare_mergeable_station(temp_dir, replacement_duration=2.2)

            with self.assertRaisesRegex(MergeError, "Agent Output Validation failed"):
                merge_station(station, source_video=source_video)

            self.assertFalse((station / "merge-output" / "merged-output.mp4").exists())


if __name__ == "__main__":
    unittest.main()
