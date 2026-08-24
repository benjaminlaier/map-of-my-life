# Map of My Life

A local-first photo map for exploring trips through geotagged photographs. The project imports photo metadata locally, displays it on an OpenStreetMap-based map, and can generate a static viewer for sharing.

## Features

- EXIF GPS and Google Photos JSON sidecar import
- Country, date, and map-viewport filtering
- Local thumbnails and full-photo viewing
- Capture location, time, and available camera metadata
- Static trip export for Firebase Hosting

## Requirements

- Conda
- Python 3.11
- Node.js and Firebase CLI only for publishing

Create the environment:

```powershell
conda env create -f environment.yml
conda activate mapofmylife
```

For an existing environment:

```powershell
conda env update -n mapofmylife -f environment.yml
conda activate mapofmylife
```

## Run locally

```powershell
python server.py
```

Open http://localhost:8000.

## Import photos

Use a Google Takeout folder or another folder containing supported image files. Keep Google Photos JSON sidecars next to their images when available.

```powershell
python importer.py "C:\path\to\your\photo-folder"
```

The importer stores metadata and generated thumbnails in the ignored `data/` directory. Original images stay in their existing location.

## Create a shareable export

Generate a static viewer containing located photos, resized web images, thumbnails, and metadata:

```powershell
python export_trip.py share
```

Test it locally:

```powershell
python -m http.server 8001 --directory share
```

Open http://localhost:8001.

The generated `share/` directory is ignored by Git because it contains personal photos.

## Publish with Firebase Hosting

Install Node.js and the Firebase CLI:

```powershell
npm install -g firebase-tools
firebase login
```

Initialize Hosting once, selecting `share` as the public directory. Choose **No** when asked to configure a single-page app, and do not overwrite the existing `share/index.html`.

```powershell
firebase init hosting
firebase deploy --only hosting
```

Firebase prints the public `web.app` URL after deployment. Anyone who has the URL can view the exported photos, so only publish images intended for sharing.

## Privacy

Photo data, generated exports, Firebase caches, and local Python files are excluded from Git. Review `git status` before pushing changes. The source repository contains the application code and configuration, not your personal photo library.

## License

This project is licensed under the [MIT License](LICENSE).

The MIT License applies to this project's source code. External dependencies and services, including Leaflet, OpenStreetMap map data and tiles, Firebase Hosting, Google Fonts, and any images included in a personal export, remain subject to their own licenses and terms. Do not publish personal photos unless you have permission to share them.