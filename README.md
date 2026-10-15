# 📚 Antigravity Comic Chronology Finder & Bulk Downloader

An intelligent comic run finder and downloader powered by the **Antigravity AI Advisor** and **Open Digital Comic Archives**.
Enter any comic title, character, or storyline, receive canonical reading orders sorted in chronological order, interactively select the issues you want to read, and download them cleanly into a dedicated folder.

---

## 🔒 Features

1. **Antigravity AI Advisor**:
   Fetches canonical chronological reading orders, creative teams (writers and artists), publication years, and synopses. Supports both **Antigravity Gateway API keys** (`agy_app_...`) and standard **Google Gemini API keys** (`AIzaSy...`), with automatic fallback to direct archive matching.
2. **Open Comic Archive Search & Format Prioritization**:
   Searches digital comic archives and strictly prioritizes formats: **CBZ > CBR > ZIP > PDF**.
   - If a `.cbz` or `.cbr` version exists for an issue or run, any redundant `.pdf` duplicate is automatically suppressed.
   - `.pdf` is kept strictly as a fallback if no digital comic archive format is available.
   - Comic scan `.zip` files are automatically handled as `.cbz`.
3. **Chronological Issue Display**:
   Automatically orders all available issues chronologically by publication year and issue number.
4. **Interactive Checkbox Selector**:
   A terminal UI (TUI) selector allowing you to navigate with arrow keys (`↑`/`↓`), toggle selection with `SPACE`, select all (`A`), deselect all (`N`), or select by comma-separated numbers / ranges (e.g. `1-4, 6`).
5. **Approval Confirmation Gate ("Click Yes")**:
   Before downloading, displays a review card of selected issues, total size in MB, and destination folder. Downloads proceed only after you confirm (`[Y/n]` / Yes).
6. **Dedicated Folder Organization**:
   Automatically creates a cleanly named folder (e.g. `downloads/Spider-Man Blue (2002)`) and streams downloads with active progress bars.

---

## 🚀 Usage

### 1. Interactive Mode
Run the script directly:
```bash
python comic_downloader.py
```
*(or run `python comic.py`)*

1. Enter your comic name or run (e.g., `Batman: Year One`, `Spider-Man Blue`, `Flashpoint`, `Court of Owls`).
2. When prompted, enter your Antigravity API key (you can choose to save it to `.env` so you don't have to enter it again).
3. Use the arrow keys and `SPACE` to pick issues to read, then press `ENTER`.
4. Review the download card and confirm with `Y`.

### 2. Direct CLI Query Mode
```bash
python comic_downloader.py "Batman: Year One"
```
Or with an API key directly:
```bash
python comic_downloader.py "Spider-Man Blue" --key YOUR_ANTIGRAVITY_API_KEY
```

---

## 🔑 API Key Configuration Options

You can provide your Antigravity API key in any of the following ways:
1. **Interactive Prompt**: The script prompts you on first run and offers to save it to `.env`.
2. **Environment Variable**: Set `ANTIGRAVITY_APP_KEY=your_key` or `AGY_API_KEY=your_key`.
3. **Command Line Flag**: Pass `--key your_key`.
4. **Local `.env` File**: Create `.env` in this directory:
   ```env
   ANTIGRAVITY_APP_KEY=your_key_here
   ```

---

## 🧪 Running Tests

To verify the installation and archive discovery:
```bash
python tests/test_comic_downloader.py
```
