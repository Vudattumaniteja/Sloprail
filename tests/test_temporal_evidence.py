from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.temporal_evidence import build_temporal_evidence


def write_frame(path: Path, color: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (80, 45), color).save(path)


class TemporalEvidenceTests(unittest.TestCase):
    def test_builds_marked_frames_and_temporal_strip_with_timing_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            first = station / "visual-evidence" / "representative-frames" / "rep-001.jpg"
            second = station / "visual-evidence" / "representative-frames" / "rep-002.jpg"
            write_frame(first, "red")
            write_frame(second, "blue")

            kept_frames = [
                {
                    "id": "rep-001",
                    "path": "visual-evidence/representative-frames/rep-001.jpg",
                    "coverage_span": {
                        "id": "span-001",
                        "station_local_start_seconds": 0.0,
                        "station_local_end_seconds": 4.0,
                        "source_start_seconds": 12.0,
                        "source_end_seconds": 16.0,
                    },
                },
                {
                    "id": "rep-002",
                    "path": "visual-evidence/representative-frames/rep-002.jpg",
                    "coverage_span": {
                        "id": "span-002",
                        "station_local_start_seconds": 4.0,
                        "station_local_end_seconds": 10.0,
                        "source_start_seconds": 16.0,
                        "source_end_seconds": 22.0,
                    },
                },
            ]

            evidence = build_temporal_evidence(station, kept_frames)

            self.assertEqual(evidence["temporal_strip"]["path"], "visual-evidence/temporal-strip.png")
            self.assertTrue((station / evidence["temporal_strip"]["path"]).is_file())
            self.assertEqual(len(evidence["marked_frames"]), 2)
            self.assertEqual(evidence["marked_frames"][0]["markup_status"], "no_visual_markup")
            self.assertEqual(evidence["marked_frames"][0]["coverage_span_id"], "span-001")
            self.assertTrue((station / evidence["marked_frames"][0]["path"]).is_file())
            labels = evidence["temporal_strip"]["embedded_timing_labels"]
            self.assertIn("source 12.000s-16.000s", labels[0]["label"])
            self.assertIn("local 4.000s-10.000s", labels[1]["label"])

    def test_preserves_existing_marked_frame_as_visual_markup_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            representative = station / "visual-evidence" / "representative-frames" / "rep-001.jpg"
            marked = station / "visual-evidence" / "marked-frames" / "rep-001-marked.png"
            write_frame(representative, "red")
            write_frame(marked, "green")
            before = marked.read_bytes()

            kept_frames = [
                {
                    "id": "rep-001",
                    "path": "visual-evidence/representative-frames/rep-001.jpg",
                    "coverage_span": {
                        "id": "span-001",
                        "station_local_start_seconds": 0.0,
                        "station_local_end_seconds": 4.0,
                        "source_start_seconds": 12.0,
                        "source_end_seconds": 16.0,
                    },
                }
            ]

            evidence = build_temporal_evidence(station, kept_frames)

            self.assertEqual(marked.read_bytes(), before)
            self.assertEqual(evidence["marked_frames"][0]["markup_status"], "visual_markup_present")


if __name__ == "__main__":
    unittest.main()
