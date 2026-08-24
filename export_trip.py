import argparse
import json
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent
DB_PATH = ROOT / "data" / "map-of-my-life.db"


def export_trip(destination):
    destination = Path(destination)
    images = destination / "images"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    images.mkdir()
    shutil.copy2(ROOT / "web" / "index.html", destination / "index.html")
    shutil.copy2(ROOT / "web" / "styles.css", destination / "styles.css")
    shutil.copy2(ROOT / "web" / "app.js", destination / "app.js")
    with sqlite3.connect(DB_PATH) as connection:
        columns = "id, filename, latitude, longitude, country, city, region, captured_at, camera, lens, focal_length, altitude, direction, thumbnail_path, original_path"
        rows = connection.execute(f"SELECT {columns} FROM photos WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY captured_at").fetchall()
    photos = []
    for row in rows:
        photo = {"id": row[0], "filename": row[1], "latitude": row[2], "longitude": row[3], "country": row[4] or "Unknown", "city": row[5] or "", "region": row[6] or "", "date": row[7] or "", "camera": row[8] or "", "lens": row[9] or "", "focal_length": row[10], "altitude": row[11], "direction": row[12], "thumb": f"images/{row[0]}-thumb.jpg", "full": f"images/{row[0]}.jpg"}
        thumbnail = Path(row[13])
        original = Path(row[14])
        if thumbnail.is_file():
            shutil.copy2(thumbnail, images / f"{row[0]}-thumb.jpg")
        if original.is_file():
            try:
                from PIL import Image, ImageOps
                with Image.open(original) as image:
                    image = ImageOps.exif_transpose(image)
                    image.thumbnail((1600, 1600))
                    image.convert("RGB").save(images / f"{row[0]}.jpg", "JPEG", quality=76, optimize=True)
            except Exception:
                shutil.copy2(original, images / f"{row[0]}.jpg")
        photos.append(photo)
    (destination / "photos.json").write_text(json.dumps({"photos": photos}, ensure_ascii=True), encoding="utf-8")
    print(f"Exported {len(photos)} located photos to {destination.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a self-contained static trip viewer.")
    parser.add_argument("destination", nargs="?", default="share", help="Output folder")
    export_trip(parser.parse_args().destination)