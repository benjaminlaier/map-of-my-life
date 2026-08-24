from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
DB_PATH = ROOT / "data" / "map-of-my-life.db"
WEB_ROOT = ROOT / "web"

DEMO_PHOTOS = [
    {"id": "demo-1", "filename": "Cusco sunrise.jpg", "latitude": -13.53195, "longitude": -71.96746, "country": "Peru", "date": "2024-05-18", "thumb": "https://images.unsplash.com/photo-1530789253388-582c481c54b0?w=640&q=80"},
    {"id": "demo-2", "filename": "Lake Titicaca.jpg", "latitude": -15.84022, "longitude": -70.02188, "country": "Peru", "date": "2024-05-22", "thumb": "https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?w=640&q=80"},
    {"id": "demo-3", "filename": "Atacama evening.jpg", "latitude": -23.65093, "longitude": -70.3975, "country": "Chile", "date": "2024-06-02", "thumb": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=640&q=80"},
    {"id": "demo-4", "filename": "Patagonia trail.jpg", "latitude": -50.94233, "longitude": -73.40679, "country": "Chile", "date": "2024-06-15", "thumb": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=640&q=80"},
    {"id": "demo-5", "filename": "Buenos Aires walk.jpg", "latitude": -34.60372, "longitude": -58.38159, "country": "Argentina", "date": "2024-06-25", "thumb": "https://images.unsplash.com/photo-1589909202802-8f4aadce1849?w=640&q=80"},
]


def load_photos():
    if not DB_PATH.exists():
        return DEMO_PHOTOS
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT id, filename, latitude, longitude, country, city, region, captured_at, camera, lens, focal_length, altitude, direction FROM photos WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY captured_at"
        ).fetchall()
    return [
        {"id": row[0], "filename": row[1], "latitude": row[2], "longitude": row[3], "country": row[4] or "Unknown", "city": row[5] or "", "region": row[6] or "", "date": row[7] or "", "camera": row[8] or "", "lens": row[9] or "", "focal_length": row[10], "altitude": row[11], "direction": row[12], "thumb": ""}
        for row in rows
    ] or DEMO_PHOTOS


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/api/photos":
            payload = json.dumps({"photos": load_photos()}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if route.startswith("/api/photo/"):
            parts = route.strip("/").split("/")
            photo_id = parts[2] if len(parts) > 2 else ""
            if DB_PATH.exists():
                with sqlite3.connect(DB_PATH) as connection:
                    column = "thumbnail_path" if len(parts) > 3 and parts[3] == "thumbnail" else "original_path"
                    row = connection.execute(f"SELECT {column} FROM photos WHERE id = ?", (photo_id,)).fetchone()
                if row:
                    photo_path = Path(row[0]).resolve()
                    if photo_path.is_file():
                        content = photo_path.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-Type", mimetypes.guess_type(photo_path.name)[0] or "application/octet-stream")
                        self.send_header("Content-Length", str(len(content)))
                        self.end_headers()
                        self.wfile.write(content)
                        return
            self.send_error(404, "Photo not found")
            return
        super().do_GET()

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    WEB_ROOT.mkdir(exist_ok=True)
    print("Bizzies Trips running at http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), AppHandler).serve_forever()
