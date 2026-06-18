from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.run_e2e_station_demo import run_demo


ROOT = Path(__file__).resolve().parents[1]


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


@unittest.skipUnless(has_ffmpeg(), "ffmpeg and ffprobe are required for the end-to-end Station demo")
class EndToEndStationDemoTests(unittest.TestCase):
    def test_runs_fixture_backed_station_demo(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            output_root = Path(temp_dir) / "issue-10-e2e-station-demo"

            report = run_demo(output_root, force=False)
            key_outputs = report["key_outputs"]
            station_folder = output_root / "stations" / "station-e2e-001"

            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["station_handoff_validation"]["issue_count"], 0)
            self.assertEqual(report["agent_output_validation"]["issue_count"], 0)
            self.assertTrue(report["agent_output_validation"]["merge_allowed"])
            self.assertEqual(report["final_station_handoff_validation"]["issue_count"], 0)
            self.assertTrue((output_root / "demo-report.json").is_file())
            self.assertTrue((station_folder / "review-notes.json").is_file())
            self.assertTrue((station_folder / "merge-output" / "merged-output.mp4").is_file())
            self.assertTrue((station_folder / "merge-output" / "normalization-report.md").is_file())

            for relative_path in key_outputs.values():
                self.assertTrue(Path(relative_path).is_file())


if __name__ == "__main__":
    unittest.main()
