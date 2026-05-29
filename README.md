# YTS-Plex-RSS

Finds movies that are missing from your Plex library in 1080p (via YTS) and serves them as an RSS feed for your torrent client to auto-download.

## Features

- Scans your Plex library for missing 1080p movies
- Searches YTS for matching torrents
- Generates a clean RSS feed
- Easy integration with Sonarr/Radarr or any torrent client
- Lightweight and runs on a schedule

## Installation

```bash
git clone https://github.com/drew-codes-things/YTS-Plex-RSS.git
cd YTS-Plex-RSS
pip install -r requirements.txt
```

## Usage

Configure your Plex token and library path in `config.py`, then run:
```bash
python app.py
```

The RSS feed will be available at `http://localhost:5000/rss`

## Requirements

- Python 3.8+
- Plex server with API access
- YTS access (no API key needed)

## License

MIT License