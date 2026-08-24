# Map of My Life

A local-first photo map for exploring journeys with exact photo locations.

## Run the prototype

```powershell
python server.py
```

Open http://localhost:8000.

The first screen uses a small South America demo dataset. To create the Conda environment from scratch, run:

```powershell
conda env create -f environment.yml
conda activate mapofmylife
```

If the environment already exists, update it with:

```powershell
conda env update -n mapofmylife -f environment.yml
```

To import a Google Takeout folder, run:

```powershell
python importer.py "C:\path\to\Google Photos"
python server.py
```

## Create a shareable trip

After importing, create a self-contained static viewer:

```powershell
python export_trip.py share
```

Test the export locally:

```powershell
python -m http.server 8001 --directory share
```

Open http://localhost:8001. The `share/` folder contains the map, metadata, thumbnails, and web-sized originals. It is excluded from Git because it contains personal photos.

To publish it with Firebase Hosting, install Node.js and the Firebase CLI, then run from the project folder:

```powershell
npm install -g firebase-tools
firebase login
firebase init hosting
```

When Firebase asks for the public directory, enter `share` and choose the single-page app option if prompted. Then publish with:

```powershell
firebase deploy
```

Firebase will provide an unlisted `web.app` URL that can be shared with family. Anyone with that URL can view the export, so do not include photos that should remain private.

## Current scope

- Local SQLite metadata database
- EXIF GPS and Google Photos JSON sidecar import
- OpenStreetMap tiles through Leaflet
- Country and date filtering
- Local-first visual map with an image detail panel

Original photo files stay where they are; the importer stores their paths and metadata. Thumbnail generation and private share links are next milestones.

For further updates
python importer.py "C:\Users\Benjamin Laier\Pictures\MapTest"
python export_trip.py share
firebase deploy --only hosting