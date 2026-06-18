from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from scripts.validate_station_folder import validate_project_or_station
from scripts.visual_canvas_markup import save_marked_frame, station_payload


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "tests" / "fixtures" / "station-folders" / "canonical-station-001"


def changed_png_bytes() -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
    try:
        image = Image.new("RGBA", (80, 45), "white")
        draw = ImageDraw.Draw(image)
        draw.ellipse((12, 8, 62, 38), outline="red", width=5)
        image.save(temp_path, format="PNG")
        return temp_path.read_bytes()
    finally:
        temp_path.unlink(missing_ok=True)


class VisualCanvasMarkupTests(unittest.TestCase):
    def test_saves_visual_markup_as_marked_frame_without_mutating_representative(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            representative_path = station / "visual-evidence" / "representative-frames" / "rep-001.jpg"
            before = representative_path.read_bytes()

            marked = save_marked_frame(station, "rep-001", changed_png_bytes())

            self.assertEqual(marked["markup_status"], "visual_markup_present")
            self.assertEqual(marked["path"], "visual-evidence/marked-frames/rep-001-marked.png")
            self.assertEqual(representative_path.read_bytes(), before)
            self.assertEqual(validate_project_or_station(station), [])

            station_json = json.loads((station / "station.json").read_text(encoding="utf-8"))
            rep = station_json["visual_evidence"]["representative_frames"][0]
            self.assertEqual(rep["marked_frame_id"], "rep-001-marked")

    def test_no_visual_markup_writes_explicit_marked_frame_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            station = Path(temp_dir) / "station"
            shutil.copytree(CANONICAL, station)
            marked = save_marked_frame(station, "rep-002")

            self.assertEqual(marked["markup_status"], "no_visual_markup")
            with Image.open(station / "visual-evidence" / "representative-frames" / "rep-002.jpg") as clean:
                with Image.open(station / marked["path"]) as saved:
                    diff = ImageChops.difference(clean.convert("RGBA"), saved.convert("RGBA"))
                    self.assertIsNone(diff.getbbox())
            self.assertEqual(validate_project_or_station(station), [])

    def test_station_payload_lists_representative_frames_for_browser_selection(self) -> None:
        payload = station_payload(CANONICAL)

        self.assertEqual(payload["station_id"], "station-001")
        self.assertEqual(payload["representative_frames"][0]["id"], "rep-001")
        self.assertEqual(payload["representative_frames"][0]["marked_frame_path"], "visual-evidence/marked-frames/rep-001-marked.png")


if __name__ == "__main__":
    unittest.main()
