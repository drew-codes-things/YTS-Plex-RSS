# YTS-Plex-RSS

A Python tool that scans a Plex library for missing 1080p movies using the YTS catalogue and exposes them via a web dashboard and an RSS feed for qBittorrent auto-downloading.

## Overview

The tool consists of two scripts:

- yts_check.py: Performs the scan against Plex and YTS, maintains missing_1080p.json
- yts_rss.py: Flask application providing the web UI and RSS feed

## API Endpoints

The Flask server (yts_rss.py) exposes the following endpoints:

- GET / : Serves the main web dashboard. Displays a table of missing movies with search, sorting, pagination, statistics, and bulk actions. Renders server-side using Jinja2 templates.
- POST /delete/<item_id> : Removes a single movie entry by its UUID from the missing list and redirects to the dashboard.
- POST /delete_bulk : Accepts a JSON array of IDs in the form field "ids" and removes multiple entries.
- GET /yts_missing.rss : Returns a valid RSS 2.0 feed containing all missing movies. Each item includes title, description (size and year), magnet link as enclosure, and tor: namespace extensions for magnetURI and infoHash to support qBittorrent's auto-downloader.

The RSS feed uses the namespace http://toradio.org/2010/torrent for torrent-specific metadata.

## External APIs

- YTS Movies API (https://movies-api.accel.li/api/v2/list_movies.json): Used to fetch 1080p movie listings. Supports parameters such as quality, limit (50 per page), page, sort_by (year or download_count), and order. The scanner uses pagination with resume support via scan_state.json.
- Jikan API (https://api.jikan.moe/v4/anime): Optional anime filter endpoint. Queries by title and checks release year proximity to skip anime titles when USE_MAL_FILTER=true. Responses are cached in mal_cache.json.
- Plex API (via plexapi library): Connects using X-Plex-Token to enumerate movies in the specified library section and check videoResolution == "1080".

## Features

- Configurable fast mode (MIN_YEAR) or full catalogue scan with progress saving
- Automatic pruning of titles that appear in Plex
- Optional MyAnimeList-based anime filtering with rate limiting and caching
- Magnet links pre-built with 13 public trackers
- Dark-themed responsive web UI with client-side sorting, filtering, and bulk operations
- Standards-compliant RSS feed consumable by qBittorrent

## Setup

### Prerequisites

- Python 3.8+
- Plex server with API token access
- qBittorrent with RSS support (optional but recommended)

### Installation

```bash
git clone https://github.com/drew-codes-things/YTS-Plex-RSS.git
cd YTS-Plex-RSS
pip install -r requirements.txt
```

Create a requirements.txt file containing:

flask
python-dotenv
plexapi
tqdm
requests
markupsafe

### Configuration

Copy .env.example to .env and edit:

```
PLEX_USER_TOKEN=your_token
PLEX_SERVER_NAME=YourServer
LIBRARY_NAME=Movies
MIN_YEAR=2025
SLEEP_SECONDS=1.2
USE_MAL_FILTER=false
```

To obtain a Plex token: In Plex Web, select any media item, click Get Info, then View XML. The X-Plex-Token value in the resulting URL is the required token.

## Running

Run the scanner periodically:

python yts_check.py

Start the server:

python yts_rss.py

Access the dashboard at http://localhost:5000

Subscribe to the RSS feed at http://localhost:5000/yts_missing.rss inside qBittorrent.

## Project Structure

- yts_check.py - Scanner and data processor
- yts_rss.py - Flask web and RSS server
- missing_1080p.json - Generated list of missing items
- scan_state.json - Resume state for full scans
- mal_cache.json - Cached anime detection results
- .env.example - Configuration template

## License

MIT License