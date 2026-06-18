from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_station_folder import validate_project_or_station


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "tests" / "fixtures" / "station-folders" / "canonical-station-001"


def issue_codes(path: Path) -> set[str]:
    return {issue.code for issue in validate_project_or_station(path)}


class StationFolderValidatorTests(unittest.TestCase):
    def test_canonical_station_folder_passes(self) -> None:
        self.assertEqual(validate_project_or_station(CANONICAL), [])

    def test_missing_required_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            (station / "README.md").unlink()

            self.assertIn("missing_file", issue_codes(station))

    def test_empty_notes_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            (station / "notes.md").write_text("   \n", encoding="utf-8")

            self.assertIn("empty_station_level_note", issue_codes(station))

    def test_missing_notes_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            (station / "notes.md").unlink()

            self.assertIn("missing_file", issue_codes(station))

    def test_html_preview_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            (station / "preview.html").write_text("<!doctype html>", encoding="utf-8")

            self.assertIn("html_preview_out_of_scope", issue_codes(station))

    def test_unresolved_station_json_path_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            station_json_path = station / "station.json"
            station_json = json.loads(station_json_path.read_text(encoding="utf-8"))
            station_json["visual_evidence"]["temporal_strip"]["path"] = "visual-evidence/missing-temporal-strip.png"
            station_json_path.write_text(json.dumps(station_json, indent=2), encoding="utf-8")

            self.assertIn("unresolved_path_reference", issue_codes(station))

    def test_overlapping_station_target_windows_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            first = project / "stations" / "station-001"
            second = project / "stations" / "station-002"
            shutil.copytree(CANONICAL, first)
            shutil.copytree(CANONICAL, second)

            station_json_path = second / "station.json"
            station_json = json.loads(station_json_path.read_text(encoding="utf-8"))
            station_json["station_id"] = "station-002"
            station_json["target_window"]["source_start_seconds"] = 16.0
            station_json["target_window"]["source_end_seconds"] = 25.0
            station_json_path.write_text(json.dumps(station_json, indent=2), encoding="utf-8")

            self.assertIn("overlapping_station_target_windows", issue_codes(project))

    def test_multiple_source_videos_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            first = project / "stations" / "station-001"
            second = project / "stations" / "station-002"
            shutil.copytree(CANONICAL, first)
            shutil.copytree(CANONICAL, second)

            station_json_path = second / "station.json"
            station_json = json.loads(station_json_path.read_text(encoding="utf-8"))
            station_json["station_id"] = "station-002"
            station_json["source_video"]["id"] = "source-video-002"
            station_json["source_video"]["path"] = "visual-evidence/source-window.mp4"
            station_json["target_window"]["source_start_seconds"] = 30.0
            station_json["target_window"]["source_end_seconds"] = 40.0
            station_json_path.write_text(json.dumps(station_json, indent=2), encoding="utf-8")

            self.assertIn("multiple_source_videos", issue_codes(project))

    def test_invalid_target_window_timing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            station_json_path = station / "station.json"
            station_json = json.loads(station_json_path.read_text(encoding="utf-8"))
            station_json["target_window"]["source_end_seconds"] = 11.0
            station_json_path.write_text(json.dumps(station_json, indent=2), encoding="utf-8")

            self.assertIn("invalid_target_window_timing", issue_codes(station))

    def test_target_window_duration_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            station_json_path = station / "station.json"
            station_json = json.loads(station_json_path.read_text(encoding="utf-8"))
            station_json["target_window"]["duration_seconds"] = 8.5
            station_json_path.write_text(json.dumps(station_json, indent=2), encoding="utf-8")

            self.assertIn("invalid_target_window_timing", issue_codes(station))

    def test_missing_context_requires_station_json_and_readme_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            (station / "README.md").write_text("# Station\n\nNo partial context declaration.\n", encoding="utf-8")

            self.assertIn("partial_context_not_declared_in_readme", issue_codes(station))

    def test_missing_context_requires_station_json_partial_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            station_json_path = station / "station.json"
            station_json = json.loads(station_json_path.read_text(encoding="utf-8"))
            station_json["station_context"]["partial"] = False
            station_json_path.write_text(json.dumps(station_json, indent=2), encoding="utf-8")

            self.assertIn("partial_context_not_flagged", issue_codes(station))


if __name__ == "__main__":
    unittest.main()
