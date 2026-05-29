from flask import Flask, Response, render_template_string, request, redirect
from markupsafe import Markup
import json
import os
import re
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
MISSING_JSON = "missing_1080p.json"
PAGE_SIZE = 50


def load_missing():
    try:
        with open(MISSING_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_missing(items):
    with open(MISSING_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def parse_size_bytes(size_str):
    try:
        parts = size_str.strip().split()
        val = float(parts[0])
        unit = parts[1].upper()
        multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
        return int(val * multipliers.get(unit, 0))
    except Exception:
        return 0


def fmt_bytes(b):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.2f} {unit}"
        b /= 1024
    return f"{b:.2f} PB"


def extract_infohash(magnet):
    try:
        match = re.search(r'urn:btih:([a-fA-F0-9]{40})', magnet)
        return match.group(1).upper() if match else ""
    except Exception:
        return ""


CSS = """
body {
    font-family: 'Montserrat', sans-serif;
    background-color: #121212;
    color: #f0f0f0;
    margin: 0;
    padding: 0;
    line-height: 1.6;
}
.container { max-width: 1600px; margin: 0 auto; padding: 40px 30px; }
header {
    background-image: url('banner.png');
    background-size: cover;
    background-position: center;
    text-align: center;
    position: relative;
    width: 100%;
    margin: 0 0 40px 0;
    min-height: 180px;
    display: flex;
    align-items: center;
    justify-content: center;
}
header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-color: rgba(0,0,0,0.5);
    z-index: 1;
}
header .container { position: relative; z-index: 2; padding: 20px; }
h1 {
    font-family: 'Playfair Display', serif;
    color: #8be9fd;
    font-size: clamp(2.5rem, 7vw, 4rem);
    margin: 0;
    text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;
}
h2 {
    font-family: 'Playfair Display', serif;
    color: #8be9fd;
    font-size: 2rem;
    margin-top: 0;
    margin-bottom: 20px;
    border-bottom: 2px solid #8be9fd;
    padding-bottom: 10px;
}
.section {
    background-color: #1e1e1e;
    border-radius: 12px;
    padding: 30px 40px;
    margin-bottom: 40px;
    box-shadow: 0 6px 12px rgba(0,0,0,0.4);
}
.layout {
    display: grid;
    grid-template-columns: 1fr 2.5fr 1fr;
    gap: 40px;
    align-items: start;
}
.feed { grid-column: 1 / 2; }
.main-content { grid-column: 2 / 3; }
.sidebar { grid-column: 3 / 4; }
a { color: #8b0000; text-decoration: none; transition: color 0.3s; }
a:hover { color: #c0392b; }
.btn {
    display: inline-block;
    background: #8b0000;
    color: #fff;
    border: none;
    padding: 9px 18px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background 0.2s;
}
.btn:hover { background: #a00000; }
.btn-secondary {
    background: #333;
    margin-left: 8px;
}
.btn-secondary:hover { background: #444; }
input[type=text], input[type=search] {
    background: #2a2a2a;
    border: 1px solid #444;
    color: #f0f0f0;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.95rem;
    width: 100%;
    box-sizing: border-box;
    margin-bottom: 16px;
}
table { width: 100%; border-collapse: collapse; }
thead tr { border-bottom: 2px solid #8be9fd; }
th {
    text-align: left;
    padding: 12px 10px;
    color: #8be9fd;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
}
th:hover { color: #fff; }
th .sort-arrow { font-size: 0.75rem; margin-left: 4px; opacity: 0.5; }
th.sorted .sort-arrow { opacity: 1; }
tbody tr { border-bottom: 1px solid #2a2a2a; transition: background 0.15s; }
tbody tr:hover { background: #252525; }
td { padding: 13px 10px; vertical-align: middle; }
.badge {
    background: #2a2a2a;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.82rem;
    color: #ccc;
}
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.stat-box {
    background: #2a2a2a;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}
.stat-box .val { font-size: 1.6rem; font-weight: 700; color: #8be9fd; }
.stat-box .lbl { font-size: 0.8rem; color: #888; margin-top: 4px; }
.pagination { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 20px; align-items: center; }
.page-btn {
    background: #2a2a2a;
    color: #f0f0f0;
    border: none;
    padding: 7px 13px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 0.9rem;
}
.page-btn.active { background: #8b0000; }
.page-btn:hover:not(.active) { background: #333; }
#bar-chart { width: 100%; margin-top: 10px; }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 0.85rem; }
.bar-row .year-lbl { width: 42px; color: #aaa; text-align: right; flex-shrink: 0; }
.bar-fill { height: 18px; background: #8b0000; border-radius: 3px; transition: width 0.3s; min-width: 2px; }
.bar-count { color: #888; font-size: 0.8rem; }
.status-list { display: flex; flex-direction: column; gap: 10px; padding: 0; }
.status-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #2a2a2a;
    border-radius: 8px;
    padding: 12px 16px;
    list-style: none;
}
.status-badge { background: #8b0000; color: #fff; border-radius: 12px; padding: 2px 10px; font-size: 0.8rem; }
#bulk-bar {
    display: none;
    background: #1a1a1a;
    border: 1px solid #8b0000;
    border-radius: 8px;
    padding: 12px 18px;
    margin-bottom: 16px;
    align-items: center;
    gap: 14px;
}
@media (max-width: 900px) {
    .layout { grid-template-columns: 1fr; }
    .feed, .main-content, .sidebar { grid-column: 1; }
    .stat-grid { grid-template-columns: 1fr 1fr; }
}
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Missing 1080p - tisL</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>{{ css }}</style>
</head>
<body>
<header>
    <div class="container">
        <h1>Missing 1080p Movies</h1>
        <p style="color:#ccc; margin-top:8px; font-size:1.1rem;">{{ total }} titles waiting</p>
    </div>
</header>
<div class="container">
<div class="layout">

  <div>
    <div class="feed section">
      <h2>RSS Feed</h2>
      <p>Paste into qBittorrent's RSS reader for auto-download.</p>
      <code style="display:block; background:#2a2a2a; padding:10px 14px; border-radius:6px; word-break:break-all; font-size:0.88rem; margin-bottom:16px;">
        http://{{ host }}/yts_missing.rss
      </code>
      <a href="/yts_missing.rss" class="btn" style="display:block; text-align:center;">Open RSS Feed</a>
    </div>
    <div class="section">
      <h2>How to Use</h2>
      <ul class="status-list">
        <li class="status-item"><span>1. Copy RSS URL above</span><span class="status-badge">Step 1</span></li>
        <li class="status-item"><span>2. Add to qBittorrent RSS</span></li>
        <li class="status-item"><span>3. Set auto-download rule</span></li>
        <li class="status-item"><span>4. Click Remove when done</span></li>
      </ul>
    </div>
  </div>

  <div class="main-content section">
    <h2>Missing Movies</h2>
    <input type="search" id="search-box" placeholder="Search by title or year..." oninput="filterTable()">
    <div id="bulk-bar">
      <span id="bulk-count">0 selected</span>
      <form method="post" action="/delete_bulk" id="bulk-form" style="display:inline">
        <input type="hidden" name="ids" id="bulk-ids-input">
        <button type="submit" class="btn">Remove Selected</button>
      </form>
      <button class="btn btn-secondary" onclick="clearSelection()">Clear</button>
    </div>
    <table id="movies-table">
      <thead>
        <tr>
          <th style="width:36px"><input type="checkbox" id="select-all" onchange="toggleAll(this)"></th>
          <th onclick="sortTable(1)">Title <span class="sort-arrow">v</span></th>
          <th onclick="sortTable(2)" style="text-align:center">Size <span class="sort-arrow">v</span></th>
          <th onclick="sortTable(3)" style="text-align:center">Year <span class="sort-arrow">v</span></th>
          <th onclick="sortTable(4)" style="text-align:center">Added <span class="sort-arrow">v</span></th>
          <th style="text-align:center">Magnet</th>
          <th style="width:90px"></th>
        </tr>
      </thead>
      <tbody>
      {% for item in items %}
        <tr data-id="{{ item.id }}" data-year="{{ item.year }}">
          <td><input type="checkbox" class="row-cb" value="{{ item.id }}" onchange="updateBulkBar()"></td>
          <td>{{ item.title }}</td>
          <td style="text-align:center"><span class="badge">{{ item.size }}</span></td>
          <td style="text-align:center; color:#888">{{ item.year }}</td>
          <td style="text-align:center; color:#888; font-size:0.9rem">{{ item.added[:10] }}</td>
          <td style="text-align:center"><a href="{{ item.magnet }}">Magnet</a></td>
          <td style="text-align:center">
            <form method="post" action="/delete/{{ item.id }}" style="margin:0">
              <button type="submit" class="btn">Remove</button>
            </form>
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    <div class="pagination" id="pagination"></div>
  </div>

  <div>
    <div class="section">
      <h2>Stats</h2>
      <div class="stat-grid">
        <div class="stat-box"><div class="val">{{ total }}</div><div class="lbl">Missing Titles</div></div>
        <div class="stat-box"><div class="val">{{ total_size }}</div><div class="lbl">Total Size</div></div>
        <div class="stat-box"><div class="val">{{ year_range }}</div><div class="lbl">Year Range</div></div>
        <div class="stat-box"><div class="val">{{ newest_year }}</div><div class="lbl">Newest Year</div></div>
      </div>
    </div>
    <div class="section">
      <h2>By Year</h2>
      <div id="bar-chart">
        {% for year, count, pct in year_chart %}
        <div class="bar-row">
          <span class="year-lbl">{{ year }}</span>
          <div class="bar-fill" style="width:{{ pct }}%"></div>
          <span class="bar-count">{{ count }}</span>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>

</div>
</div>

<script>
const PAGE_SIZE = 50;
let currentPage = 1;
let sortCol = -1;
let sortAsc = true;
let visibleRows = [];

function parseSize(sizeStr) {
  if (!sizeStr) return 0;
  const parts = sizeStr.trim().split(/\s+/);
  if (parts.length < 2) return 0;
  let val = parseFloat(parts[0]);
  const unit = parts[1].toUpperCase();
  const multipliers = { "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4 };
  return val * (multipliers[unit] || 1);
}

function getAllRows() {
  return Array.from(document.querySelectorAll('#movies-table tbody tr'));
}

function filterTable() {
  const q = document.getElementById('search-box').value.toLowerCase();
  visibleRows = getAllRows().filter(row => {
    const title = row.cells[1].textContent.toLowerCase();
    const year = row.dataset.year;
    const match = title.includes(q) || year.includes(q);
    row.style.display = match ? '' : 'none';
    return match;
  });
  currentPage = 1;
  // Uncheck select-all when the filter changes to avoid operating on hidden rows.
  document.getElementById('select-all').checked = false;
  paginate();
}

function paginate() {
  const start = (currentPage - 1) * PAGE_SIZE;
  visibleRows.forEach((row, i) => {
    row.style.display = (i >= start && i < start + PAGE_SIZE) ? '' : 'none';
  });
  renderPagination();
}

function renderPagination() {
  const total = visibleRows.length;
  const pages = Math.ceil(total / PAGE_SIZE);
  const el = document.getElementById('pagination');
  if (pages <= 1) { el.innerHTML = ''; return; }
  let html = `<span style="color:#888;font-size:0.9rem">${total} results</span>`;
  for (let p = 1; p <= pages; p++) {
    html += `<button class="page-btn${p === currentPage ? ' active' : ''}" onclick="goPage(${p})">${p}</button>`;
  }
  el.innerHTML = html;
}

function goPage(p) {
  currentPage = p;
  paginate();
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function sortTable(col) {
  if (sortCol === col) { sortAsc = !sortAsc; } else { sortCol = col; sortAsc = true; }
  const tbody = document.querySelector('#movies-table tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  rows.sort((a, b) => {
    let av = a.cells[col].textContent.trim();
    let bv = b.cells[col].textContent.trim();
    if (col === 2) {
      av = parseSize(av);
      bv = parseSize(bv);
    } else if (col === 3) {
      av = parseInt(av) || 0;
      bv = parseInt(bv) || 0;
    } else if (col === 4) {
      av = new Date(av);
      bv = new Date(bv);
    }
    if (av < bv) return sortAsc ? -1 : 1;
    if (av > bv) return sortAsc ? 1 : -1;
    return 0;
  });
  rows.forEach(r => tbody.appendChild(r));
  document.querySelectorAll('th').forEach(th => th.classList.remove('sorted'));
  document.querySelectorAll('th')[col].classList.add('sorted');
  filterTable();
}

function toggleAll(cb) {
  // Only toggle rows that are currently visible (not hidden by the search filter).
  visibleRows.forEach(row => {
    const checkbox = row.querySelector('.row-cb');
    if (checkbox) checkbox.checked = cb.checked;
  });
  updateBulkBar();
}

function updateBulkBar() {
  const checked = document.querySelectorAll('.row-cb:checked');
  const bar = document.getElementById('bulk-bar');
  document.getElementById('bulk-count').textContent = checked.length + ' selected';
  bar.style.display = checked.length > 0 ? 'flex' : 'none';
}

function clearSelection() {
  document.querySelectorAll('.row-cb').forEach(c => c.checked = false);
  document.getElementById('select-all').checked = false;
  updateBulkBar();
}

document.getElementById('bulk-form').addEventListener('submit', function() {
  const ids = Array.from(document.querySelectorAll('.row-cb:checked')).map(c => c.value);
  document.getElementById('bulk-ids-input').value = JSON.stringify(ids);
});

visibleRows = getAllRows();
paginate();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    items = load_missing()
    total = len(items)
    total_bytes = sum(item.get("size_bytes") or parse_size_bytes(item.get("size", "")) for item in items)
    total_size = fmt_bytes(total_bytes)
    years = [item.get("year", 0) for item in items if item.get("year")]
    year_range = f"{min(years)} - {max(years)}" if years else "N/A"
    newest_year = str(max(years)) if years else "N/A"

    from collections import Counter
    year_counts = sorted(Counter(years).items(), reverse=True)
    max_count = max((c for _, c in year_counts), default=1)
    year_chart = [(y, c, round(c / max_count * 100)) for y, c in year_counts]

    return render_template_string(
        HTML_TEMPLATE,
        items=items,
        total=total,
        total_size=total_size,
        year_range=year_range,
        newest_year=newest_year,
        year_chart=year_chart,
        host=request.host,
        css=Markup(CSS),
    )


@app.route("/delete/<string:item_id>", methods=["POST"])
def delete(item_id):
    items = [i for i in load_missing() if i.get("id") != item_id]
    save_missing(items)
    return redirect("/")


@app.route("/delete_bulk", methods=["POST"])
def delete_bulk():
    raw = request.form.get("ids", "[]")
    try:
        ids = set(json.loads(raw))
    except Exception:
        ids = set()
    items = [i for i in load_missing() if i.get("id") not in ids]
    save_missing(items)
    return redirect("/")


def _item_pub_date(item):
    """Return RFC-2822 pub date from the item's 'added' timestamp, falling back to now."""
    added = item.get("added", "")
    if added:
        try:
            dt = datetime.fromisoformat(added)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except (ValueError, TypeError):
            pass
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


@app.route("/yts_missing.rss")
def rss():
    items = load_missing()
    host = request.host
    base_url = f"http://{host}"

    rss_items = ""
    for item in items:
        pub_date = _item_pub_date(item)
        magnet = item["magnet"]
        title = item["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        infohash = extract_infohash(magnet)
        year_val = item.get("year", "N/A")

        rss_items += f"""
  <item>
    <title>{title}</title>
    <description>Size: {item.get("size", "Unknown")} | Year: {year_val}</description>
    <link>{magnet}</link>
    <guid isPermaLink="false">{item["id"]}</guid>
    <pubDate>{pub_date}</pubDate>
    <enclosure url="{magnet}" length="{item.get('size_bytes', 0)}" type="application/x-bittorrent"/>
    <tor:magnetURI>{magnet}</tor:magnetURI>
    <tor:infoHash>{infohash}</tor:infoHash>
  </item>"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:tor="http://toradio.org/2010/torrent">
  <channel>
    <title>Star's Missing 1080p YTS Movies</title>
    <description>Auto-generated missing 1080p movies from YTS -> Plex</description>
    <link>{base_url}</link>
    <atom:link href="{base_url}/yts_missing.rss" rel="self" type="application/rss+xml"/>
    <lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
{rss_items}
  </channel>
</rss>"""

    return Response(rss_xml, mimetype="application/rss+xml")


if __name__ == "__main__":
    print("Star's YTS -> PLEX -> RSS Tool")
    print("   -> Web UI   : http://127.0.0.1:5000")
    print("   -> RSS Feed : http://127.0.0.1:5000/yts_missing.rss")
    app.run(host="0.0.0.0", port=5000, debug=False)
