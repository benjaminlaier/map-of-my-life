import argparse
import hashlib
import json
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}
DB_PATH = Path(__file__).parent / "data" / "map-of-my-life.db"
THUMBNAIL_DIR = Path(__file__).parent / "data" / "thumbnails"


def read_exif(path):
    try:
        from PIL import Image, ExifTags
        image = Image.open(path)
        raw = image.getexif()
        tags = {ExifTags.TAGS.get(key, key): value for key, value in raw.items()}
        exif_ifd = raw.get_ifd(34665)
        tags.update({ExifTags.TAGS.get(key, key): value for key, value in exif_ifd.items()})
        gps_ifd = raw.get_ifd(34853)
        gps = {ExifTags.GPSTAGS.get(key, key): value for key, value in gps_ifd.items()}
        def number(value):
            return float(value[0]) / float(value[1]) if hasattr(value, "__len__") else float(value)

        metadata = {
            "camera": " ".join(filter(None, [tags.get("Make"), tags.get("Model")])) or None,
            "lens": tags.get("LensModel") or tags.get("LensSpecification"),
            "focal_length": number(tags["FocalLength"]) if tags.get("FocalLength") is not None else None,
            "altitude": number(gps["GPSAltitude"]) if gps.get("GPSAltitude") is not None else None,
            "direction": number(gps["GPSImgDirection"]) if gps.get("GPSImgDirection") is not None else None,
            "date": tags.get("DateTimeOriginal") or tags.get("DateTime"),
        }
        if not gps:
            return None, None, metadata

        latitude = sum(number(part) / (60 ** index) for index, part in enumerate(gps.get("GPSLatitude", [])))
        longitude = sum(number(part) / (60 ** index) for index, part in enumerate(gps.get("GPSLongitude", [])))
        if gps.get("GPSLatitudeRef") == "S": latitude *= -1
        if gps.get("GPSLongitudeRef") == "W": longitude *= -1
        return latitude, longitude, metadata
    except Exception:
        return None, None, {"camera": None, "lens": None, "focal_length": None, "altitude": None, "direction": None, "date": None}


def read_sidecar(path):
    sidecar = path.with_name(path.name + ".json")
    if not sidecar.exists():
        sidecar = path.with_suffix(path.suffix + ".json")
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        location = data.get("geoDataExif") or data.get("geoData") or {}
        return location.get("latitude"), location.get("longitude"), data.get("photoTakenTime", {}).get("timestamp")
    except (OSError, json.JSONDecodeError):
        return None, None, None


def normalize_date(value):
    if not value:
        return ""
    if len(value) >= 19 and value[4] == ":" and value[7] == ":":
        return value.replace(":", "-", 2)
    return value


def lookup_location(latitude, longitude, cache):
    key = (round(latitude, 1), round(longitude, 1))
    if key in cache:
        return cache[key]
    query = urllib.parse.urlencode({"format": "jsonv2", "zoom": 18, "lat": latitude, "lon": longitude})
    request = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/reverse?{query}",
        headers={"User-Agent": "MapOfMyLife/0.1 personal local app"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            address = json.loads(response.read().decode("utf-8")).get("address", {})
        location = {"city": address.get("city") or address.get("town") or address.get("village") or address.get("municipality"), "region": address.get("state") or address.get("region"), "country": address.get("country") or address.get("country_code", "").upper()}
    except (OSError, json.JSONDecodeError):
        location = {"city": None, "region": None, "country": "Unknown"}
    cache[key] = location
    time.sleep(1.1)
    return location


def import_folder(folder):
    DB_PATH.parent.mkdir(exist_ok=True)
    THUMBNAIL_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("""CREATE TABLE IF NOT EXISTS photos (
        id TEXT PRIMARY KEY, filename TEXT NOT NULL, original_path TEXT NOT NULL,
        thumbnail_path TEXT, latitude REAL, longitude REAL, country TEXT,
        city TEXT, region TEXT, captured_at TEXT, camera TEXT, lens TEXT,
        focal_length REAL, altitude REAL, direction REAL, location_source TEXT,
        imported_at TEXT NOT NULL
    )""")
    existing_columns = {row[1] for row in connection.execute("PRAGMA table_info(photos)")}
    for column, data_type in {"city": "TEXT", "region": "TEXT", "camera": "TEXT", "lens": "TEXT", "focal_length": "REAL", "altitude": "REAL", "direction": "REAL"}.items():
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE photos ADD COLUMN {column} {data_type}")
    files = [path for path in Path(folder).rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS]
    located = 0
    country_cache = {}
    for path in files:
        latitude, longitude, metadata = read_exif(path)
        captured_at = metadata["date"]
        source = "exif" if latitude is not None and longitude is not None else None
        if latitude is None or longitude is None:
            latitude, longitude, timestamp = read_sidecar(path)
            if timestamp and not captured_at:
                captured_at = datetime.fromtimestamp(int(timestamp)).isoformat()
            source = "sidecar" if latitude is not None and longitude is not None else None
        captured_at = normalize_date(captured_at)
        location = lookup_location(latitude, longitude, country_cache) if latitude is not None and longitude is not None else {"city": None, "region": None, "country": None}
        photo_id = hashlib.sha1(str(path.resolve()).encode()).hexdigest()
        thumbnail_path = THUMBNAIL_DIR / f"{photo_id}.jpg"
        try:
            from PIL import Image, ImageOps
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image)
                image.thumbnail((480, 480))
                image.convert("RGB").save(thumbnail_path, "JPEG", quality=82, optimize=True)
        except Exception:
            thumbnail_path = Path("")
        connection.execute("INSERT OR REPLACE INTO photos (id, filename, original_path, thumbnail_path, latitude, longitude, country, city, region, captured_at, camera, lens, focal_length, altitude, direction, location_source, imported_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (photo_id, path.name, str(path.resolve()), str(thumbnail_path), latitude, longitude, location["country"], location["city"], location["region"], captured_at, metadata["camera"], metadata["lens"], metadata["focal_length"], metadata["altitude"], metadata["direction"], source, datetime.now().isoformat()))
        located += int(latitude is not None and longitude is not None)
    connection.commit()
    connection.close()
    print(f"Scanned {len(files)} photos: {located} with coordinates, {len(files) - located} without coordinates.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import vacation photos and their location metadata into Bizzies Trips.")
    parser.add_argument("folder", help="Google Takeout or local photo folder")
    import_folder(parser.parse_args().folder)
