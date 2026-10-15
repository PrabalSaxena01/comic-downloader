# 📚 Antigravity Comic Chronology Finder & Bulk Downloader

An intelligent comic run finder and bulk downloader powered by the **Antigravity Safe Keyless Virtual Middleware** and **Open Digital Comic Archives**.
Enter any comic title, character, storyline, or era (e.g. `X men Krakoa era`, `Batman Year One`, `House of X`), receive canonical reading orders sorted in chronological order, interactively select the issues you want to read, and download them cleanly into a dedicated folder.

---

## 🛡️ Core Architecture: Zero Client Keys

Following the hardened architecture in `antigravity_server/Instruction`:
- **No Secret Client Keys Stored**: Authorization is handled automatically via a high-entropy 128-bit public route slug (`/p/pub_.../v1`).
- **Token Drain Guard Compliance**: Uses `effort: "low"` and bounded payloads to prevent unnecessary compute exhaustion.
- **Universal Connection**: Works seamlessly locally (`http://127.0.0.1:8000/p/<slug>/v1`), across home Wi-Fi LAN, or remotely over secure Cloudflare Tunnels (`https://<tunnel>.trycloudflare.com/p/<slug>/v1`).

---

## 🔒 Features

1. **Antigravity AI Advisor**:
   Fetches canonical chronological reading orders, creative teams (writers and artists), publication years, and continuity synopses via the Keyless Virtual Middleware endpoint.
   - Automatically breaks down complex multi-series comic eras (e.g. *Krakoa Era*, *Dawn of X*, *Secret Wars*) into their essential chronological issues.
   - Falls back gracefully to authenticated API keys, local `agy` CLI, or direct archive matching if the gateway is offline.
2. **Open Comic Archive Search & Format Prioritization**:
   Searches digital comic archives and strictly prioritizes formats: **CBZ > CBR > ZIP > PDF**.
   - If a `.cbz` or `.cbr` version exists for an issue or run, redundant `.pdf` duplicates are automatically suppressed.
   - `.pdf` is kept strictly as a fallback if no digital comic archive format is available.
   - Comic scan `.zip` files are automatically handled as `.cbz`.
3. **Chronological Issue Display**:
   Automatically orders all available issues chronologically by publication year and issue number.
4. **Interactive Checkbox Selector**:
   A terminal UI (TUI) selector allowing you to navigate with arrow keys (`↑`/`↓`), toggle selection with `SPACE`, select all (`A`), deselect all (`N`), or select by comma-separated numbers / ranges (e.g. `1-4, 6`).
5. **Approval Confirmation Gate ("Click Yes")**:
   Before downloading, displays a review card of selected issues, total size in MB, and destination folder. Downloads proceed only after you confirm (`[Y/n]` / Yes).
6. **Dedicated Folder Organization**:
   Automatically creates a cleanly named folder (e.g. `downloads/X Men Krakoa Era (2019)`) and streams downloads with active progress bars.

---

## 🚀 Quick Start

### 1. Zero-Key Run
The downloader connects to your Antigravity Virtual Middleware out-of-the-box:
```bash
python comic_downloader.py
```
*(or run `python comic.py`)*

### 2. Direct Query
```bash
python comic_downloader.py "X men Krakoa era"
```

### 3. Remote Cloudflare Tunnel Endpoint
If running against a remote Antigravity server via Cloudflare Tunnel:
```bash
python comic_downloader.py "House of X" --endpoint https://<your-tunnel>.trycloudflare.com/p/pub_b93935784aff3f67d55d904e7e43f30f/v1
```

---

## ⚙️ Configuration (`.env`)

Configure your connection settings in `.env`:
```ini
# Safe Keyless Virtual Middleware Endpoint (Zero Client Keys)
ANTIGRAVITY_ENDPOINT=http://127.0.0.1:8000/p/pub_b93935784aff3f67d55d904e7e43f30f/v1

# AI Model Selection
ANTIGRAVITY_MODEL=gemini-2.5-flash
```

---

## 🧪 Running Tests

To verify the installation, format prioritization, and Virtual Middleware integration:
```bash
python tests/test_comic_downloader.py
```
