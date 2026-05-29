# YTS-Plex-RSS

Compares your Plex movie library against the YTS torrent catalogue and
serves an RSS feed of missing titles so you can auto-download them with
qBittorrent (or any RSS-capable torrent client).

---

## How It Works

The project is split into two independent scripts that work together:

```
yts_check.py  ->  missing_1080p.json  ->  yts_rss.py
(nightly cron)    (shared data file)       (persistent web server)
```

1. **`yts_check.py`** - the data-gathering script. Run this (manually or on a schedule) to:
   - Connect to your Plex server and list every movie already in your library.
   - Scan YTS for movies that match your quality/year filters but are not in Plex.
   - Write the results to `missing_1080p.json`.

2. **`yts_rss.py`** - the web server / RSS feed. Run this as a persistent process. It:
   - Reads `missing_1080p.json` on every request (no restart needed after a check run).
   - Exposes a web UI at `http://<host>:5000` and an RSS feed at `http://<host>:5000/yts_missing.rss`.
   - Lets you remove titles from the list via the UI or in bulk.

**You must run `yts_check.py` at least once before `yts_rss.py` has anything to serve.**

---

## Installation

```bash
git clone https://github.com/drew-codes-things/YTS-Plex-RSS.git
cd YTS-Plex-RSS

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your Plex token and preferences
```

### Get your Plex token

Sign in to [plex.tv](https://plex.tv), open any media item, click the three-dot menu -> Get Info -> View XML. The token is the `X-Plex-Token` value in the URL.

---

## Quick Start

```bash
# Step 1 - populate the missing-movies list
python yts_check.py

# Step 2 - start the RSS / web server
python yts_rss.py
```

Open `http://127.0.0.1:5000` in your browser, then paste
`http://<your-ip>:5000/yts_missing.rss` into qBittorrent's RSS reader.

---

## Environment Variables

Copy `.env.example` to `.env` and set the values below.

| Variable | Type | Default | Description |
|---|---|---|---|
| `PLEX_USER_TOKEN` | string | (required) | Your Plex authentication token |
| `PLEX_SERVER_NAME` | string | `Epos` | Friendly name of your Plex server as shown in plex.tv |
| `LIBRARY_NAME` | string | `Movies` | Name of the Plex library section to scan |
| `MIN_YEAR` | integer | `0` | Only include YTS movies from this year onwards; `0` = scan entire catalogue (slow, resumes across runs) |
| `SLEEP_SECONDS` | float | `1.2` | Delay in seconds between YTS API page requests - increase if you hit rate limits |
| `USE_MAL_FILTER` | boolean | `false` | Skip movies that appear on MyAnimeList (anime filter); queries `api.jikan.moe` |
| `QUALITY` | string | `1080p` | Torrent quality to search for. Allowed values: `720p`, `1080p`, `2160p` |

---

## Automating with Cron

Run `yts_check.py` on a schedule (e.g. nightly at 02:00) so `missing_1080p.json`
stays up to date without any manual effort.

### Add a crontab entry

```bash
crontab -e
```

Paste the line below, adjusting the path to match your actual install location:

```cron
# Run the YTS check every night at 02:00
0 2 * * * /path/to/venv/bin/python /path/to/YTS-Plex-RSS/yts_check.py >> /path/to/YTS-Plex-RSS/yts_check.log 2>&1
```

The `>> ... 2>&1` part appends all output (stdout + stderr) to a log file
so you can inspect past runs with `tail -f yts_check.log`.

---

## Running `yts_rss.py` as a Persistent Service

`yts_rss.py` needs to stay running so the RSS feed and web UI are always
available. There are two common approaches:

### Option A - systemd (recommended on Linux servers)

Create `/etc/systemd/system/yts-rss.service`:

```ini
[Unit]
Description=YTS Plex RSS Feed
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/YTS-Plex-RSS
ExecStart=/path/to/venv/bin/python /path/to/YTS-Plex-RSS/yts_rss.py
Restart=on-failure
EnvironmentFile=/path/to/YTS-Plex-RSS/.env

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable yts-rss
sudo systemctl start yts-rss
sudo systemctl status yts-rss
```

### Option B - keep-alive in a terminal (quick/dev use)

```bash
# Linux / macOS
nohup python yts_rss.py > yts_rss.log 2>&1 &

# Or with screen
screen -S yts-rss
python yts_rss.py
# Ctrl+A then D to detach
```

---

## File Reference

```
YTS-Plex-RSS/
    yts_check.py        # Data-gathering script (run on a schedule)
    yts_rss.py          # Web server + RSS feed (run persistently)
    .env                # Your local config (copy from .env.example)
    .env.example        # Template with all supported env vars
    requirements.txt    # Python dependencies
    missing_1080p.json  # Auto-generated: movies to download
    scan_state.json     # Auto-generated: YTS page resume state
    mal_cache.json      # Auto-generated: MAL lookup cache
    LICENSE
```

---

## Requirements

- Python 3.8+
- A Plex Media Server accessible from the machine running this tool
- Dependencies: `flask`, `requests`, `plexapi`, `tqdm`, `python-dotenv`, `markupsafe`

---

## License

MIT License
