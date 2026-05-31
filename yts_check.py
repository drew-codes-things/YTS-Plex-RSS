import time
import json
import requests
import os
import re
import uuid
from urllib.parse import quote_plus
from datetime import datetime, timezone
from plexapi.myplex import MyPlexAccount
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

PLEX_USER_TOKEN = os.getenv("PLEX_USER_TOKEN")
PLEX_SERVER_NAME = os.getenv("PLEX_SERVER_NAME", "Epos")
LIBRARY_NAME = os.getenv("LIBRARY_NAME", "Movies")
MIN_YEAR = int(os.getenv("MIN_YEAR", 2025))
SLEEP_SECONDS = float(os.getenv("SLEEP_SECONDS", 1.2))
USE_MAL_FILTER = os.getenv("USE_MAL_FILTER", "false").lower() == "true"
QUALITY = os.getenv("QUALITY", "1080p")

MISSING_JSON = "missing_1080p.json"
SCAN_STATE_FILE = "scan_state.json"
MAL_CACHE_FILE = "mal_cache.json"

BASE_URL = "https://movies-api.accel.li/api/v2/list_movies.json"
MAL_SEARCH_URL = "https://api.jikan.moe/v4/anime"

BRANDING = "Star's YTS -> PLEX -> RSS Tool"

MAL_CACHE = {}


def _normalise_title(title):
    """Lowercase, strip punctuation/spaces for fuzzy comparison."""
    return re.sub(r'[^a-z0-9]', '', title.lower())


def load_mal_cache():
    global MAL_CACHE
    try:
        with open(MAL_CACHE_FILE, "r", encoding="utf-8") as f:
            MAL_CACHE = json.load(f)
    except Exception:
        MAL_CACHE = {}


def save_mal_cache():
    try:
        with open(MAL_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(MAL_CACHE, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def is_anime_on_mal(title, year):
    """Return True only if the title matches a MAL anime entry of type 'Movie'
    within 2 years of the given year.

    Using limit=5 instead of 1 to reduce false positives from partial title
    matches. Only entries where mal_entry["type"] == "Movie" are considered,
    so TV series and OVAs with similar names do not flag real movies as anime.
    """
    if not USE_MAL_FILTER:
        return False

    key = f"{title.strip().lower()}_{year}"
    if key in MAL_CACHE:
        return MAL_CACHE[key]

    try:
        params = {"q": title, "limit": 5}
        r = requests.get(MAL_SEARCH_URL, params=params, timeout=8)
        if r.status_code == 200:
            results = r.json().get("data", [])
            for mal_entry in results:
                if mal_entry.get("type") != "Movie":
                    continue
                mal_year = mal_entry.get("year") or (mal_entry.get("aired", {}).get("from") or "")[:4]
                try:
                    if mal_year and abs(int(mal_year) - year) <= 2:
                        MAL_CACHE[key] = True
                        save_mal_cache()
                        time.sleep(0.35)
                        return True
                except (ValueError, TypeError):
                    pass
        MAL_CACHE[key] = False
    except Exception:
        MAL_CACHE[key] = False

    save_mal_cache()
    time.sleep(0.35)
    return False


def get_local_1080p_movies_from_plex():
    print(f"\n{BRANDING}")
    print("=" * 70)
    print("Connecting to Plex...")
    account = MyPlexAccount(token=PLEX_USER_TOKEN)
    server = account.resource(PLEX_SERVER_NAME).connect()
    movies_section = server.library.section(LIBRARY_NAME)
    print(f"Scanning Plex library '{LIBRARY_NAME}'...")
    local = set()
    for video in movies_section.all():
        if video.type != "movie":
            continue
        title = video.title.strip()
        year = video.year if video.year else 0
        has_quality = any(media.videoResolution == "1080" for media in video.media)
        if has_quality:
            local.add((title.lower(), year))
    print(f"Found {len(local)} {QUALITY} movies in Plex.")
    return local


def title_matches_plex(yts_title, year, local_movies):
    """Return True if yts_title/year is already in the Plex library.

    Tries an exact lower-case match first, then a punctuation-stripped
    fuzzy match so 'Spider-Man' matches 'Spider Man' etc.
    """
    lower = yts_title.lower()
    if (lower, year) in local_movies:
        return True
    norm_yts = _normalise_title(yts_title)
    for plex_title, plex_year in local_movies:
        if plex_year == year and _normalise_title(plex_title) == norm_yts:
            return True
    return False


def build_magnet(hash_str, title):
    trackers = [
        "udp://tracker.opentrackr.org:1337/announce",
        "udp://tracker.torrent.eu.org:451/announce",
        "udp://tracker.dler.org:6969/announce",
        "udp://open.stealth.si:80/announce",
        "udp://open.demonii.com:1337/announce",
        "https://tracker.moeblog.cn:443/announce",
        "udp://open.dstud.io:6969/announce",
        "udp://tracker.srv00.com:6969/announce",
        "https://tracker.zhuqiy.com:443/announce",
        "https://tracker.pmman.tech:443/announce",
        "udp://tracker.openbittorrent.com:80/announce",
        "udp://tracker.zer0day.to:1337/announce",
        "udp://exodus.desync.com:6969/announce",
    ]
    tr = "&tr=".join(quote_plus(t) for t in trackers)
    dn = quote_plus(title)
    return f"magnet:?xt=urn:btih:{hash_str}&dn={dn}&tr={tr}"


def load_scan_state():
    try:
        with open(SCAN_STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"last_page": 1}


def save_scan_state(state):
    with open(SCAN_STATE_FILE, "w") as f:
        json.dump(state, f)


def fetch_movies():
    movies = []

    if MIN_YEAR > 0:
        sort_by, order = "year", "desc"
        print(f"\nFAST MODE: Only {MIN_YEAR}+ movies (newest first)")
        start_page = 1
    else:
        sort_by, order = "download_count", "desc"
        print("\nFULL MODE: Scanning ALL movies on YTS")
        state = load_scan_state()
        start_page = state.get("last_page", 1)
        if start_page > 1:
            print(f"Resuming from page {start_page}...")

    params = {"quality": QUALITY, "limit": 50, "page": 1, "sort_by": sort_by, "order": order}
    try:
        r = requests.get(BASE_URL, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        print(f"Failed to fetch first YTS page: {e}")
        return movies

    movie_count = data.get("data", {}).get("movie_count", 0)
    total_pages = (movie_count + 49) // 50
    print(f"YTS total: {movie_count:,} movies across {total_pages} pages")

    if start_page == 1:
        movies.extend(data.get("data", {}).get("movies", []))

    pbar = tqdm(range(max(2, start_page), total_pages + 1), desc="YTS Scan", unit="page")
    for page in pbar:
        params["page"] = page
        try:
            r = requests.get(BASE_URL, params=params, timeout=20)
            r.raise_for_status()
            page_movies = r.json().get("data", {}).get("movies", [])
            if not page_movies:
                break
            movies.extend(page_movies)

            if MIN_YEAR <= 0:
                save_scan_state({"last_page": page})

            if MIN_YEAR > 0:
                page_years = [m.get("year", 0) for m in page_movies if m.get("year")]
                if page_years and min(page_years) < MIN_YEAR:
                    tqdm.write(f"[OK] Reached movies before {MIN_YEAR} -- stopping early.")
                    break

            time.sleep(SLEEP_SECONDS)
        except Exception as e:
            tqdm.write(f"Error on page {page}: {e} -- progress saved.")
            break
    else:
        save_scan_state({"last_page": 1})

    print(f"Finished fetching {len(movies):,} movies.")
    return movies


def load_missing():
    if not os.path.exists(MISSING_JSON):
        return []
    try:
        with open(MISSING_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"WARNING: {MISSING_JSON} is corrupted ({e}). Starting with empty list.")
        return []
    except Exception as e:
        print(f"WARNING: Could not read {MISSING_JSON}: {e}. Starting with empty list.")
        return []


def save_missing(items):
    with open(MISSING_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def prune_already_on_plex(local_movies, items):
    """Remove entries from the missing list that are now present in Plex.

    Uses the raw item title (e.g. 'Suzume (2022)') passed through
    title_matches_plex which handles normalisation internally. The year
    field on each item is used directly, keeping key format consistent
    with how new items are added (raw title + year).
    """
    before = len(items)
    pruned = [
        item for item in items
        if not title_matches_plex(item["title"], item.get("year", 0), local_movies)
    ]
    removed = before - len(pruned)
    if removed:
        print(f"Auto-removed {removed} titles now present in Plex.")
    return pruned


def main():
    global MAL_CACHE
    load_mal_cache()
    local_movies = get_local_1080p_movies_from_plex()
    existing_missing = load_missing()

    existing_missing = prune_already_on_plex(local_movies, existing_missing)
    save_missing(existing_missing)

    existing_keys = {(item["title"].lower().strip(), item.get("year", 0)) for item in existing_missing}

    print("\nStarting YTS scan...")
    yts_movies = fetch_movies()

    new_items = []
    skipped_plex = 0
    filtered_anime = 0
    filtered_other = 0

    if USE_MAL_FILTER:
        print(f"\nChecking {len(yts_movies):,} movies against MyAnimeList...")
        movie_iter = tqdm(yts_movies, desc="MAL Anime Filter", unit="movie")
    else:
        movie_iter = yts_movies

    for movie in movie_iter:
        try:
            title = movie.get("title")
            year = movie.get("year")
            if not title or not year or (MIN_YEAR > 0 and year < MIN_YEAR):
                filtered_other += 1
                continue

            if title_matches_plex(title, year, local_movies):
                skipped_plex += 1
                continue

            display_title = f"{title} ({year})"
            key = (display_title.lower().strip(), year)
            if key in existing_keys:
                skipped_plex += 1
                continue

            if USE_MAL_FILTER and is_anime_on_mal(title, year):
                filtered_anime += 1
                continue

            torrents = [t for t in movie.get("torrents", []) if t.get("quality") == QUALITY]
            if not torrents:
                filtered_other += 1
                continue

            best = max(torrents, key=lambda t: int(t.get("size_bytes", 0)))
            magnet = build_magnet(best["hash"], display_title)

            new_items.append({
                "id": str(uuid.uuid4()),
                "title": display_title,
                "size": best.get("size", "Unknown"),
                "size_bytes": int(best.get("size_bytes", 0)),
                "magnet": magnet,
                "added": datetime.now(timezone.utc).isoformat(),
                "year": year,
            })
            existing_keys.add(key)
        except Exception:
            filtered_other += 1
            continue

    if new_items:
        existing_missing.extend(new_items)
        save_missing(existing_missing)
        print(f"Added {len(new_items)} new missing movies.")

    save_mal_cache()

    print("\n" + "=" * 70)
    print(f"{BRANDING}")
    print(f"Scanned from YTS       : {len(yts_movies):,}")
    print(f"Already in Plex/list   : {skipped_plex:,}")
    print(f"Filtered (Anime)       : {filtered_anime:,}")
    print(f"Filtered (other)       : {filtered_other:,}")
    print(f"New missing            : {len(new_items):,}")
    print(f"Total missing now      : {len(existing_missing):,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
