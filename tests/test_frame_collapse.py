from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from scripts.frame_collapse import (
    build_candidates,
    choose_representative_candidates,
    coverage_spans,
    hamming_distance,
    perceptual_hash,
    report_for,
    write_kept_frames,
)


def write_striped_image(path: Path, inverted: bool = False) -> None:
    image = Image.new("RGB", (64, 64), "black" if inverted else "white")
    draw = ImageDraw.Draw(image)
    fill = "white" if inverted else "black"
    for x in range(0, 64, 16):
        draw.rectangle([x, 0, x + 7, 63], fill=fill)
    image.save(path)


class FrameCollapseTests(unittest.TestCase):
    def test_identical_frames_are_near_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first.jpg"
            second = root / "second.jpg"
            write_striped_image(first)
            write_striped_image(second)

            self.assertEqual(hamming_distance(perceptual_hash(first), perceptual_hash(second)), 0)

    def test_distinct_frames_do_not_collapse_under_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first.jpg"
            second = root / "second.jpg"
            write_striped_image(first)
            write_striped_image(second, inverted=True)

            self.assertGreater(hamming_distance(perceptual_hash(first), perceptual_hash(second)), 5)

    def test_quality_ranked_selection_rejects_near_duplicate_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "candidate-0001.jpg"
            duplicate = root / "candidate-0002.jpg"
            distinct = root / "candidate-0003.jpg"
            write_striped_image(first)
            write_striped_image(duplicate)
            write_striped_image(distinct, inverted=True)

            candidates = build_candidates([first, duplicate, distinct], source_start_seconds=12.0, sampling_rate_fps=2.0)
            kept, rejected = choose_representative_candidates(candidates, hash_distance_threshold=5)

            self.assertEqual([candidate.candidate_id for candidate in kept], ["candidate-0001", "candidate-0003"])
            self.assertEqual(len(rejected), 1)
            self.assertEqual(rejected[0].candidate.candidate_id, "candidate-0002")
            self.assertEqual(rejected[0].hamming_distance, 0)

    def test_report_shape_includes_manual_representative_frame_support_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            visual_evidence = station / "visual-evidence"
            source_window = visual_evidence / "source-window.mp4"
            source_window.parent.mkdir(parents=True)
            source_window.write_text("placeholder", encoding="utf-8")

            first = Path(temp_dir) / "candidate-0001.jpg"
            duplicate = Path(temp_dir) / "candidate-0002.jpg"
            distinct = Path(temp_dir) / "candidate-0003.jpg"
            write_striped_image(first)
            write_striped_image(duplicate)
            write_striped_image(distinct, inverted=True)

            candidates = build_candidates([first, duplicate, distinct], source_start_seconds=12.0, sampling_rate_fps=2.0)
            kept, rejected = choose_representative_candidates(candidates, hash_distance_threshold=5)
            spans = coverage_spans(kept, source_start_seconds=12.0, target_duration_seconds=10.0)
            kept_frames = write_kept_frames(kept, spans, visual_evidence / "representative-frames")
            report = report_for(
                station_folder=station,
                source_window=source_window,
                sampling_rate_fps=2.0,
                hash_distance_threshold=5,
                target_duration_seconds=10.0,
                candidates=candidates,
                kept_frames=kept_frames,
                rejected_frames=rejected,
            )

            self.assertEqual(report["sampling"]["candidate_count"], 3)
            self.assertEqual(report["representative_candidate_selection"]["kept_count"], 2)
            self.assertEqual(report["representative_candidate_selection"]["rejected_near_duplicate_count"], 1)
            self.assertEqual(report["representative_candidate_selection"]["manual_representative_frames"], [])
            self.assertEqual(report["kept_frames"][0]["coverage_span"]["source_start_seconds"], 12.0)
            self.assertEqual(report["kept_frames"][-1]["coverage_span"]["source_end_seconds"], 22.0)


if __name__ == "__main__":
    unittest.main()
