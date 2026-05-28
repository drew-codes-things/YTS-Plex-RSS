# YTS → Plex → RSS

A two-part Python tool that scans your **Plex library** for missing 1080p movies, cross-references them against the **YTS catalogue**, and serves the results as a live **RSS feed** you can point directly at qBittorrent for auto-downloading.

---

## How It Works

### `yts_check.py` — Scanner
Connects to your Plex server via the Plex API and builds a list of every 1080p movie you already own. It then pages through the YTS API (with resume support so you can stop and continue full scans), compares the two lists, and writes any missing titles — along with their magnet links — to `missing_1080p.json`.

Key behaviours:
- **Fast mode** — set `MIN_YEAR` to a recent year (e.g. `2024`) to only scan new releases, newest-first.
- **Full mode** — set `MIN_YEAR=0` to scan the entire YTS catalogue; progress is saved to `scan_state.json` so crashes don't lose your place.
- **Auto-prune** — titles that have appeared in Plex since the last scan are automatically removed from the missing list.
- **Anime filter** — optionally queries the MyAnimeList/Jikan API to skip anime movies (`USE_MAL_FILTER=true`).
- Builds clean magnet links with 13 public trackers attached.

### `yts_rss.py` — Web UI & RSS Server
A Flask web app that reads `missing_1080p.json` and exposes two things:

1. **Web dashboard** at `/` — a dark-themed UI showing all missing movies with sortable columns (title, size, year, date added), live search, paginated results (50/page), per-movie stats by year, and one-click or bulk removal.
2. **RSS feed** at `/yts_missing.rss` — a valid RSS 2.0 feed with magnet enclosures and `tor:` namespace extensions, consumable directly by qBittorrent's RSS auto-downloader.

---

## Setup

### 1. Install dependencies

```bash
pip install flask plexapi requests tqdm python-dotenv markupsafe
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```env
PLEX_USER_TOKEN=your_plex_token_here
PLEX_SERVER_NAME=YourServerName
LIBRARY_NAME=Movies
MIN_YEAR=0          # 0 = full scan; set e.g. 2024 for fast/recent-only mode
SLEEP_SECONDS=1.2   # delay between YTS API pages (be polite)
USE_MAL_FILTER=false  # true = skip anime movies via Jikan/MAL
```

> **Finding your Plex token:** Go to any media item in Plex Web → ⋮ → Get Info → View XML. The token is the `X-Plex-Token` value in the URL.

### 3. Run the scanner

```bash
python yts_check.py
```

This produces/updates `missing_1080p.json`. Run it periodically (e.g. via cron) to keep the list fresh.

### 4. Start the web server

```bash
python yts_rss.py
```

The app starts on `http://0.0.0.0:5000`.

---

## Using with qBittorrent

1. Open qBittorrent → **View → RSS Reader**
2. Add a new feed: `http://<your-server-ip>:5000/yts_missing.rss`
3. Set up an **Auto Downloading Rule** matching all items in the feed
4. qBittorrent will pick up new entries automatically
5. Once a movie downloads and appears in Plex, re-run `yts_check.py` — it will prune it from the list and the RSS feed

---

## File Overview

| File | Purpose |
|---|---|
| `yts_check.py` | Scans Plex + YTS, writes `missing_1080p.json` |
| `yts_rss.py` | Flask server — web UI + RSS feed |
| `missing_1080p.json` | Generated — list of missing movies with magnets |
| `scan_state.json` | Generated — stores resume page for full scans |
| `.env.example` | Template for environment variables |

---

## Notes

- The YTS API endpoint used is `movies-api.accel.li` (a public mirror).
- The RSS feed uses the `tor:` namespace (`http://toradio.org/2010/torrent`) for magnet URI and infohash fields — this is what qBittorrent reads for auto-downloading.
- Run `yts_rss.py` behind a reverse proxy (e.g. Nginx + Tailscale) if you want to access it remotely.

---

## License

MIT
