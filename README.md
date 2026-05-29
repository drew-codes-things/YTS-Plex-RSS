# YTS-Plex-RSS

Finds movies missing from your Plex library in 1080p via YTS and serves them as an RSS feed for torrent auto-downloaders (Sonarr, Radarr, qBittorrent, etc.).

## What it does

Scans your Plex library, identifies movies without a 1080p version, searches YTS for matching torrents, and generates a clean RSS feed.

## Technical Architecture

- **Backend**: Python + Flask
- **Plex Integration**: Uses Plex API to read library and check resolutions
- **YTS Integration**: Scrapes or queries YTS for 1080p torrents
- **Output**: RSS 2.0 feed at `/rss`
- **Scheduling**: Designed to run periodically (cron or systemd timer recommended)

## Key Features

- Automatic detection of missing 1080p movies
- YTS torrent matching by title + year
- Clean, filterable RSS feed
- Easy integration with *arr stack or any RSS-capable torrent client

## File Structure

```
YTS-Plex-RSS/
├── app.py
├── requirements.txt
├── config.py
├── README.md
└── LICENSE
```

## Installation (Recommended: Virtual Environment)

### On Linux / macOS

```bash
git clone https://github.com/drew-codes-things/YTS-Plex-RSS.git
cd YTS-Plex-RSS

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### On Windows

```bash
git clone https://github.com/drew-codes-things/YTS-Plex-RSS.git
cd YTS-Plex-RSS

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

## Configuration

Edit `config.py` with your Plex server URL, token, and library settings.

## Usage

```bash
python app.py
```

The RSS feed will be available at `http://localhost:5000/rss`.

## Requirements

- Python 3.8+
- Plex Media Server with API access

## License

MIT License