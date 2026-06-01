<div align="center">

# YTS-Plex-RSS

**Compares your Plex library against YTS and serves missing titles as an RSS feed.**

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/powered%20by-Flask-000000?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

</div>

---

## What it does

A two-script workflow: the first script cross-references your Plex movie library with YTS and produces a JSON list of 1080p titles you're missing. The second script reads that JSON and serves a local web UI plus an RSS feed — subscribe it to your torrent client or RSS reader to auto-grab new releases.

## Workflow

```
yts_check.py  →  missing_1080p.json  →  yts_rss.py  →  RSS feed
```

| Script | Purpose |
|---|---|
| `yts_check.py` | Polls Plex + YTS API, writes `missing_1080p.json` |
| `yts_rss.py` | Serves a web UI + RSS feed from the JSON data file |

---

## Setup

```bash
git clone https://github.com/drew-codes-things/YTS-Plex-RSS
cd YTS-Plex-RSS
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your Plex details:

```env
PLEX_USER_TOKEN=your_plex_token
PLEX_SERVER_NAME=Your Server Name
LIBRARY_NAME=Movies
```

---

## Usage

```bash
# Step 1: build the missing titles list
python yts_check.py

# Step 2: start the RSS server
python yts_rss.py
```

Then subscribe your torrent client or RSS reader to:

```
http://127.0.0.1:5000/yts_missing.rss
```

---

## Dependencies

```
flask
python-dotenv
plexapi
tqdm
requests
markupsafe
```

---

## License

MIT — made by [Drew](https://github.com/drew-codes-things)
