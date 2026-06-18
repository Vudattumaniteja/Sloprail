from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.review_notes import ReviewNotesError, write_human_review_note
from scripts.validate_station_folder import validate_project_or_station


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "tests" / "fixtures" / "station-folders" / "canonical-station-001"


def issue_codes(path: Path) -> set[str]:
    return {issue.code for issue in validate_project_or_station(path)}


class HumanReviewNotesTests(unittest.TestCase):
    def copy_station(self, temp_dir: str) -> Path:
        station = Path(temp_dir) / "station"
        shutil.copytree(CANONICAL, station)
        return station

    def test_writes_station_local_and_matching_source_video_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)

            path = write_human_review_note(
                station_folder=station,
                review_subject="merged_output",
                station_local_time_seconds=2.5,
                category="fps",
                observation="Motion becomes choppy after normalization.",
            )

            payload = json.loads(path.read_text(encoding="utf-8"))
            note = payload["notes"][0]
            self.assertEqual(note["station_local_time_seconds"], 2.5)
            self.assertEqual(note["source_video_time_seconds"], 14.5)
            self.assertEqual(note["category"], "fps")
            self.assertEqual(validate_project_or_station(station), [])

    def test_rejects_unknown_category(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)

            with self.assertRaisesRegex(ReviewNotesError, "category must be one of"):
                write_human_review_note(
                    station_folder=station,
                    review_subject="merged_output",
                    station_local_time_seconds=1.0,
                    category="audio",
                    observation="Narration is out of sync.",
                )

    def test_rejects_station_local_time_outside_target_window(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)

            with self.assertRaisesRegex(ReviewNotesError, "inside the Target Window"):
                write_human_review_note(
                    station_folder=station,
                    review_subject="replacement_render",
                    station_local_time_seconds=10.5,
                    category="visual",
                    observation="The replacement misses the marked screen area.",
                )

    def test_supports_normalization_report_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)

            path = write_human_review_note(
                station_folder=station,
                review_subject="merged_output",
                station_local_time_seconds=4.0,
                category="visual",
                observation="Edges shimmer after frame-rate normalization.",
                normalization_report_path="merge-output/normalization-report.md",
                normalization_report_detail="frame_rate: 15/1 -> 30/1",
            )

            note = json.loads(path.read_text(encoding="utf-8"))["notes"][0]
            self.assertEqual(note["normalization_report_reference"]["path"], "merge-output/normalization-report.md")
            self.assertEqual(validate_project_or_station(station), [])

    def test_validator_rejects_mismatched_source_video_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            payload = json.loads((station / "review-notes.json").read_text(encoding="utf-8"))
            payload["notes"].append(
                {
                    "id": "review-note-001",
                    "review_subject": "merged_output",
                    "station_local_time_seconds": 2.0,
                    "source_video_time_seconds": 99.0,
                    "category": "general",
                    "observation": "Timecode mismatch fixture.",
                }
            )
            (station / "review-notes.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

            self.assertIn("invalid_review_timecode", issue_codes(station))


if __name__ == "__main__":
    unittest.main()
