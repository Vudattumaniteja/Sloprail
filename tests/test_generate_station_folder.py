from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.generate_station_folder import StationRequest, generate_station_folder, probe_media
from scripts.validate_station_folder import validate_project_or_station


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


@unittest.skipUnless(has_ffmpeg(), "ffmpeg and ffprobe are required for Source Video extraction tests")
class GenerateStationFolderTests(unittest.TestCase):
    def make_source_video(self, path: Path) -> None:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc=size=160x90:rate=10:duration=4",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1000:duration=4",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def write_context(self, folder: Path, name: str, body: str) -> Path:
        path = folder / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_generates_valid_station_folder_with_source_window_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_video = root / "source.mp4"
            self.make_source_video(source_video)

            output_folder = root / "stations" / "station-issue-04"
            generated = generate_station_folder(
                StationRequest(
                    source_video=source_video,
                    output_folder=output_folder,
                    station_id="station-issue-04",
                    source_video_id="source-video-issue-04",
                    source_start_seconds=1.0,
                    source_end_seconds=3.0,
                    station_level_note="Replace the Target Window with a cleaner product-table render.",
                    full_transcript=self.write_context(root, "full-transcript.md", "Full Source Video transcript.\n"),
                    target_window_transcript=self.write_context(root, "target-window-transcript.md", "Target Window transcript.\n"),
                    storyline=self.write_context(root, "storyline.md", "Storyline snapshot.\n"),
                )
            )

            self.assertEqual(generated, output_folder)
            self.assertEqual(validate_project_or_station(output_folder), [])
            self.assertTrue((output_folder / "visual-evidence" / "source-window.mp4").is_file())
            self.assertTrue(probe_media(output_folder / "visual-evidence" / "source-window.mp4")["audio_present"])

            station_json = json.loads((output_folder / "station.json").read_text(encoding="utf-8"))
            self.assertEqual(station_json["source_video"]["path"], "visual-evidence/source-window.mp4")
            self.assertEqual(station_json["target_window"]["station_local_start_seconds"], 0.0)
            self.assertEqual(station_json["target_window"]["station_local_end_seconds"], 2.0)
            self.assertEqual(station_json["read_boundary"]["scope"], "station-folder-only")
            self.assertTrue(station_json["station_context"]["partial"])
            self.assertEqual(station_json["station_context"]["missing"], ["design-rules.md"])
            self.assertIn("Partial Station Context", (output_folder / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
