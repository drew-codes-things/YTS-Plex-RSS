# YTS-Plex-RSS

Two-script workflow that compares Plex movies with YTS and exposes an RSS feed of missing titles.

## Workflow

1. Run `yts_check.py` to create/update `missing_1080p.json`.
2. Run `yts_rss.py` to serve UI + RSS feed from that data file.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` with Plex settings (`PLEX_USER_TOKEN`, `PLEX_SERVER_NAME`, `LIBRARY_NAME`, etc.).

## Run

```bash
python yts_check.py
python yts_rss.py
```

RSS endpoint:

`http://127.0.0.1:5000/yts_missing.rss`

## Dependencies

See `requirements.txt`:
- flask
- python-dotenv
- plexapi
- tqdm
- requests
- markupsafe

## License

MIT

