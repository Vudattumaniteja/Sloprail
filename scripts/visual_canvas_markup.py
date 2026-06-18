from __future__ import annotations

import argparse
import base64
import io
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from PIL import Image

try:
    from validate_station_folder import validate_project_or_station
except ModuleNotFoundError:
    from scripts.validate_station_folder import validate_project_or_station


MARKUP_STATUS_NONE = "no_visual_markup"
MARKUP_STATUS_PRESENT = "visual_markup_present"


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def load_station(station_folder: Path) -> dict[str, Any]:
    station_path = station_folder / "station.json"
    return json.loads(station_path.read_text(encoding="utf-8"))


def write_station(station_folder: Path, station: dict[str, Any]) -> None:
    (station_folder / "station.json").write_text(json.dumps(station, indent=2), encoding="utf-8")


def resolve_station_path(station_folder: Path, path_ref: str) -> Path:
    if Path(path_ref).is_absolute():
        raise ValueError("Station path references must be relative.")
    resolved = (station_folder / path_ref).resolve()
    resolved.relative_to(station_folder.resolve())
    return resolved


def image_bytes_to_png(image_bytes: bytes) -> bytes:
    with Image.open(io.BytesIO(image_bytes)) as image:
        output = io.BytesIO()
        image.convert("RGBA").save(output, format="PNG")
        return output.getvalue()


def data_url_to_bytes(data_url: str) -> bytes:
    prefix = "data:image/png;base64,"
    if not data_url.startswith(prefix):
        raise ValueError("Visual Markup image data must be a PNG data URL.")
    return base64.b64decode(data_url[len(prefix) :], validate=True)


def find_representative_frame(station: dict[str, Any], representative_frame_id: str) -> dict[str, Any]:
    visual_evidence = station.get("visual_evidence")
    if not isinstance(visual_evidence, dict):
        raise ValueError("station.json must contain visual_evidence.")
    frames = visual_evidence.get("representative_frames")
    if not isinstance(frames, list):
        raise ValueError("station.json must contain representative_frames.")
    for frame in frames:
        if isinstance(frame, dict) and frame.get("id") == representative_frame_id:
            return frame
    raise ValueError(f"Representative Frame not found: {representative_frame_id}")


def upsert_marked_frame(station: dict[str, Any], marked_frame: dict[str, Any]) -> None:
    visual_evidence = station.setdefault("visual_evidence", {})
    marked_frames = visual_evidence.setdefault("marked_frames", [])
    if not isinstance(marked_frames, list):
        raise ValueError("visual_evidence.marked_frames must be a list.")

    for index, existing in enumerate(marked_frames):
        if isinstance(existing, dict) and existing.get("id") == marked_frame["id"]:
            marked_frames[index] = marked_frame
            return
    marked_frames.append(marked_frame)


def save_marked_frame(
    station_folder: Path,
    representative_frame_id: str,
    markup_png_bytes: bytes | None = None,
) -> dict[str, Any]:
    station_folder = station_folder.resolve()
    station = load_station(station_folder)
    representative = find_representative_frame(station, representative_frame_id)

    representative_path = resolve_station_path(station_folder, representative["path"])
    marked_dir = station_folder / "visual-evidence" / "marked-frames"
    marked_dir.mkdir(parents=True, exist_ok=True)
    marked_path = marked_dir / f"{representative_frame_id}-marked.png"

    if markup_png_bytes is None:
        with Image.open(representative_path) as image:
            image.convert("RGBA").save(marked_path, format="PNG")
        markup_status = MARKUP_STATUS_NONE
    else:
        marked_path.write_bytes(image_bytes_to_png(markup_png_bytes))
        markup_status = MARKUP_STATUS_PRESENT

    coverage_span = representative.get("coverage_span")
    if not isinstance(coverage_span, dict) or not isinstance(coverage_span.get("id"), str):
        raise ValueError("Representative Frame must declare a Coverage Span before markup can be saved.")

    marked_frame = {
        "id": f"{representative_frame_id}-marked",
        "representative_frame_id": representative_frame_id,
        "coverage_span_id": coverage_span["id"],
        "path": relative(marked_path, station_folder),
        "markup_status": markup_status,
    }
    representative["marked_frame_id"] = marked_frame["id"]
    upsert_marked_frame(station, marked_frame)
    write_station(station_folder, station)

    issues = validate_project_or_station(station_folder)
    if issues:
        rendered = "\n".join(f"{item.code}: {item.path}: {item.message}" for item in issues)
        raise RuntimeError(f"Saved Marked Frame failed Station Handoff Validation:\n{rendered}")
    return marked_frame


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sloprail Visual Canvas</title>
  <style>
    :root { color-scheme: light; font-family: Arial, sans-serif; }
    body { margin: 0; background: #f5f5f2; color: #171717; }
    header, main { max-width: 1120px; margin: 0 auto; padding: 16px; }
    header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
    h1 { font-size: 22px; margin: 0; }
    .layout { display: grid; grid-template-columns: 220px 1fr; gap: 16px; }
    .frames { display: grid; gap: 8px; align-content: start; }
    button { border: 1px solid #222; background: #fff; border-radius: 6px; padding: 9px 12px; cursor: pointer; }
    button:focus-visible, input:focus-visible { outline: 3px solid #1d4ed8; outline-offset: 2px; }
    .frame-button { text-align: left; }
    .frame-button[aria-current="true"] { background: #111; color: #fff; }
    .toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
    canvas { max-width: 100%; background: #fff; border: 1px solid #222; touch-action: none; }
    .status { min-height: 20px; font-size: 14px; }
    label { display: inline-flex; align-items: center; gap: 6px; }
    @media (max-width: 760px) { .layout { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <h1>Sloprail Visual Canvas</h1>
    <div id="station"></div>
  </header>
  <main class="layout">
    <nav class="frames" id="frames" aria-label="Representative Frames"></nav>
    <section>
      <div class="toolbar">
        <button id="save">Save Visual Markup</button>
        <button id="save-none">Save No Visual Markup</button>
        <button id="reset">Reset Drawing</button>
        <label>Brush <input id="brush" type="range" min="3" max="32" value="10"></label>
        <label>Color <input id="color" type="color" value="#ff2d20"></label>
      </div>
      <canvas id="canvas" aria-label="Representative Frame markup canvas"></canvas>
      <p class="status" id="status" role="status"></p>
    </section>
  </main>
  <script>
    const framesEl = document.getElementById("frames");
    const stationEl = document.getElementById("station");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    const statusEl = document.getElementById("status");
    const brush = document.getElementById("brush");
    const color = document.getElementById("color");
    let station = null;
    let selected = null;
    let baseImage = null;
    let drawing = false;
    let dirty = false;

    function setStatus(text) { statusEl.textContent = text; }
    function drawBase() { ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.drawImage(baseImage, 0, 0); }
    function canvasPoint(event) {
      const rect = canvas.getBoundingClientRect();
      return { x: (event.clientX - rect.left) * canvas.width / rect.width, y: (event.clientY - rect.top) * canvas.height / rect.height };
    }
    function beginDraw(event) {
      if (!baseImage) return;
      drawing = true;
      dirty = true;
      const point = canvasPoint(event);
      ctx.beginPath();
      ctx.moveTo(point.x, point.y);
      event.preventDefault();
    }
    function moveDraw(event) {
      if (!drawing) return;
      const point = canvasPoint(event);
      ctx.lineWidth = Number(brush.value);
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.strokeStyle = color.value;
      ctx.lineTo(point.x, point.y);
      ctx.stroke();
      event.preventDefault();
    }
    function endDraw() { drawing = false; }

    async function loadStation() {
      const response = await fetch("/api/station");
      station = await response.json();
      stationEl.textContent = station.station_id;
      framesEl.innerHTML = "";
      station.representative_frames.forEach(frame => {
        const button = document.createElement("button");
        button.className = "frame-button";
        button.textContent = `${frame.id} (${frame.markup_status || "unsaved"})`;
        button.onclick = () => selectFrame(frame.id);
        framesEl.appendChild(button);
      });
      await selectFrame(station.representative_frames[0].id);
    }
    async function selectFrame(id) {
      selected = station.representative_frames.find(frame => frame.id === id);
      [...framesEl.children].forEach(button => button.setAttribute("aria-current", String(button.textContent.startsWith(id))));
      baseImage = new Image();
      baseImage.onload = () => {
        canvas.width = baseImage.naturalWidth;
        canvas.height = baseImage.naturalHeight;
        drawBase();
        dirty = false;
        setStatus(`Selected ${id}. Draw directly on the frame, then save.`);
      };
      baseImage.src = `/image?path=${encodeURIComponent(selected.path)}`;
    }
    async function save(noVisualMarkup) {
      if (!selected) return;
      if (!noVisualMarkup && !dirty) {
        setStatus("No drawing detected. Use Save No Visual Markup for an explicit no-markup Marked Frame.");
        return;
      }
      const payload = { representative_frame_id: selected.id, no_visual_markup: noVisualMarkup };
      if (!noVisualMarkup) payload.image_data_url = canvas.toDataURL("image/png");
      const response = await fetch("/api/marked-frame", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (!response.ok) {
        setStatus(await response.text());
        return;
      }
      const result = await response.json();
      await loadStation();
      setStatus(`Saved ${result.path} with ${result.markup_status}.`);
    }

    canvas.addEventListener("pointerdown", beginDraw);
    canvas.addEventListener("pointermove", moveDraw);
    window.addEventListener("pointerup", endDraw);
    document.getElementById("reset").onclick = () => { if (baseImage) { drawBase(); dirty = false; setStatus("Drawing reset."); } };
    document.getElementById("save").onclick = () => save(false);
    document.getElementById("save-none").onclick = () => save(true);
    loadStation().catch(error => setStatus(error.message));
  </script>
</body>
</html>
"""


class VisualCanvasHandler(BaseHTTPRequestHandler):
    station_folder: Path

    def send_bytes(self, body: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_bytes(json.dumps(payload, indent=2).encode("utf-8"), "application/json", status)

    def send_error_text(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
        self.send_bytes(message.encode("utf-8"), "text/plain; charset=utf-8", status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_bytes(HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/station":
            self.send_json(station_payload(self.station_folder))
            return
        if parsed.path == "/image":
            query = parse_qs(parsed.query)
            path_ref = query.get("path", [""])[0]
            try:
                image_path = resolve_station_path(self.station_folder, path_ref)
            except Exception as exc:
                self.send_error_text(str(exc))
                return
            content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
            self.send_bytes(image_path.read_bytes(), content_type)
            return
        self.send_error_text("Not found.", HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/marked-frame":
            self.send_error_text("Not found.", HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            representative_frame_id = payload["representative_frame_id"]
            no_visual_markup = bool(payload.get("no_visual_markup"))
            image_data = None if no_visual_markup else data_url_to_bytes(payload["image_data_url"])
            marked = save_marked_frame(self.station_folder, representative_frame_id, image_data)
        except Exception as exc:
            self.send_error_text(str(exc))
            return
        self.send_json(marked)

    def log_message(self, format: str, *args: Any) -> None:
        return


def station_payload(station_folder: Path) -> dict[str, Any]:
    station = load_station(station_folder)
    visual_evidence = station["visual_evidence"]
    marked_by_rep = {
        marked["representative_frame_id"]: marked
        for marked in visual_evidence.get("marked_frames", [])
        if isinstance(marked, dict)
    }
    frames = []
    for frame in visual_evidence["representative_frames"]:
        marked = marked_by_rep.get(frame["id"], {})
        frames.append(
            {
                "id": frame["id"],
                "path": frame["path"],
                "coverage_span": frame["coverage_span"],
                "marked_frame_id": frame.get("marked_frame_id"),
                "marked_frame_path": marked.get("path"),
                "markup_status": marked.get("markup_status"),
            }
        )
    return {"station_id": station["station_id"], "representative_frames": frames}


def serve(station_folder: Path, host: str, port: int) -> None:
    VisualCanvasHandler.station_folder = station_folder.resolve()
    server = ThreadingHTTPServer((host, port), VisualCanvasHandler)
    url = f"http://{host}:{server.server_port}/"
    print(f"Visual Canvas running at {url}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Open the Sloprail Visual Canvas markup interaction for a Station Folder.")
    parser.add_argument("--station-folder", type=Path, required=True)
    parser.add_argument("--representative-frame-id")
    parser.add_argument("--input-png", type=Path)
    parser.add_argument("--no-visual-markup", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.serve:
        serve(args.station_folder, args.host, args.port)
        return
    if not args.representative_frame_id:
        raise SystemExit("--representative-frame-id is required unless --serve is used.")
    if args.input_png and args.no_visual_markup:
        raise SystemExit("Use either --input-png or --no-visual-markup, not both.")
    image_data = None if args.no_visual_markup or args.input_png is None else args.input_png.read_bytes()
    marked = save_marked_frame(args.station_folder, args.representative_frame_id, image_data)
    print(json.dumps(marked, indent=2))


if __name__ == "__main__":
    main()
