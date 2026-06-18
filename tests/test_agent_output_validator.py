from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.validate_agent_output import validate_agent_output


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "tests" / "fixtures" / "station-folders" / "canonical-station-001"


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def issue_codes(path: Path) -> set[str]:
    return {issue.code for issue in validate_agent_output(path).issues}


def write_output_json(station: Path, payload: dict[str, object]) -> None:
    output = station / "agent-output"
    output.mkdir(exist_ok=True)
    (output / "output.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def base_payload(status: str = "completed") -> dict[str, object]:
    return {
        "schema_version": 1,
        "station_id": "station-001",
        "source_video_id": "source-video-001",
        "status": status,
    }


class AgentOutputValidatorStatusTests(unittest.TestCase):
    def copy_station(self, temp_dir: str) -> Path:
        station = Path(temp_dir) / "station"
        shutil.copytree(CANONICAL, station)
        return station

    def test_missing_output_json_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)

            self.assertIn("missing_output_json", issue_codes(station))

    def test_malformed_output_json_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            (station / "agent-output" / "output.json").write_text("{not-json", encoding="utf-8")

            self.assertIn("invalid_json", issue_codes(station))

    def test_unknown_status_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            write_output_json(station, base_payload("waiting"))

            self.assertIn("invalid_agent_output_status", issue_codes(station))

    def test_schema_version_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            payload = base_payload("blocked")
            payload.pop("schema_version")
            write_output_json(station, payload)

            self.assertIn("invalid_output_schema_version", issue_codes(station))

    def test_blocked_output_is_valid_but_not_mergeable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            write_output_json(station, base_payload("blocked"))

            result = validate_agent_output(station)
            self.assertEqual(result.issues, [])
            self.assertFalse(result.merge_allowed)
            self.assertEqual(result.status, "blocked")

    def test_failed_output_is_valid_but_not_mergeable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            write_output_json(station, base_payload("failed"))

            result = validate_agent_output(station)
            self.assertEqual(result.issues, [])
            self.assertFalse(result.merge_allowed)
            self.assertEqual(result.status, "failed")

    def test_station_identity_must_match_station_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            payload = base_payload("blocked")
            payload["station_id"] = "wrong-station"
            payload["source_video_id"] = "wrong-source"
            write_output_json(station, payload)

            codes = issue_codes(station)
            self.assertIn("station_id_mismatch", codes)
            self.assertIn("source_video_id_mismatch", codes)

    def test_completed_requires_render_and_agent_render_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            write_output_json(station, base_payload("completed"))

            codes = issue_codes(station)
            self.assertIn("missing_replacement_render", codes)
            self.assertIn("missing_agent_render_notes", codes)

    def test_output_paths_must_not_escape_station_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            payload = base_payload("blocked")
            payload["render_notes_path"] = "../render-notes.md"
            write_output_json(station, payload)

            self.assertIn("path_reference_escapes_station_folder", issue_codes(station))


@unittest.skipUnless(has_ffmpeg(), "ffmpeg and ffprobe are required for Replacement Render Media Properties tests")
class AgentOutputValidatorMediaTests(unittest.TestCase):
    def copy_station(self, temp_dir: str) -> Path:
        station = Path(temp_dir) / "station"
        shutil.copytree(CANONICAL, station)
        return station

    def make_render(self, path: Path, duration: float) -> None:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"testsrc=size=160x90:rate=100:duration={duration}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def write_completed_output(self, station: Path, duration: float) -> None:
        output = station / "agent-output"
        output.mkdir(exist_ok=True)
        self.make_render(output / "replacement-render.mp4", duration)
        (output / "render-notes.md").write_text("Agent Render Notes for the Replacement Render.\n", encoding="utf-8")
        write_output_json(station, base_payload("completed"))

    def test_completed_output_with_matching_duration_is_mergeable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            self.write_completed_output(station, 10.0)

            result = validate_agent_output(station)
            self.assertEqual(result.issues, [])
            self.assertTrue(result.merge_allowed)
            self.assertIsNotNone(result.replacement_render_media_properties)

    def test_duration_within_tolerance_is_mergeable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            self.write_completed_output(station, 10.04)

            self.assertEqual(validate_agent_output(station).issues, [])

    def test_duration_outside_tolerance_is_not_mergeable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = self.copy_station(temp_dir)
            self.write_completed_output(station, 10.2)

            result = validate_agent_output(station)
            self.assertIn("replacement_render_duration_mismatch", {issue.code for issue in result.issues})
            self.assertFalse(result.merge_allowed)


if __name__ == "__main__":
    unittest.main()
