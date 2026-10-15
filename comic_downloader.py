#!/usr/bin/env python3
"""
📚 Antigravity Comic Chronology Finder & Bulk Downloader
=========================================================
Features:
  1. AI Reading Order & Archival Dossier:
     Consults Antigravity (via API Key / Gateway or local agy CLI) to fetch canonical
     chronological reading orders, creative teams, release years, and synopses.
  2. Open Comic Archive Search:
     Searches digital comic archives (Archive.org) for .cbz, .cbr, .pdf, and .zip issues.
  3. Chronological Issue Display:
     Sorts all discovered issues by release year and issue sequence.
  4. Interactive Selection & Approval Gate:
     Interactive terminal selector (Arrow keys + Spacebar, or number ranges) with a
     mandatory confirmation prompt ('Click Yes' / [y/n]).
  5. Automated Folder Organization & Streaming Download:
     Creates a dedicated, suitably named folder and downloads all selected files with
     live progress tracking.
"""

import os
import sys
import re
import json
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_ROOT = BASE_DIR / "downloads"
DOWNLOADS_ROOT.mkdir(parents=True, exist_ok=True)
ENV_FILE = BASE_DIR / ".env"

# Virtual Middleware & Gateway Settings (Zero Client Keys Architecture)
DEFAULT_PUB_SLUG = "pub_b93935784aff3f67d55d904e7e43f30f"
DEFAULT_GATEWAY_URL = os.getenv("ANTIGRAVITY_GATEWAY_URL", "http://127.0.0.1:8000")
DEFAULT_ENDPOINT = os.getenv("ANTIGRAVITY_ENDPOINT") or os.getenv("ANTIGRAVITY_VIRTUAL_URL") or f"{DEFAULT_GATEWAY_URL}/p/{DEFAULT_PUB_SLUG}/v1"
DEFAULT_MODEL = os.getenv("ANTIGRAVITY_MODEL", "gemini-2.5-flash")


# ===================================================================
# 1. Environment & Endpoint Resolution (Zero Client Keys)
# ===================================================================

def load_local_env() -> Dict[str, str]:
    """Loads key-value pairs from local .env if present."""
    env_vars = {}
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip("'\"")
        except Exception:
            pass
    return env_vars


def save_key_to_env(key: str):
    """Saves API key to .env file for future convenience."""
    try:
        lines = []
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = [l for l in f.readlines() if not l.startswith("ANTIGRAVITY_APP_KEY=")]
        lines.append(f"ANTIGRAVITY_APP_KEY={key}\n")
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"  [✓] Antigravity API Key saved to {ENV_FILE.name}")
    except Exception as e:
        print(f"  [!] Notice: Could not write key to .env ({e})")


def resolve_virtual_middleware_url(
    endpoint: Optional[str] = None,
    pub_slug: Optional[str] = None,
    gateway_url: str = DEFAULT_GATEWAY_URL
) -> str:
    """
    Resolves the full chat completions URL for Antigravity Virtual Middleware.
    Follows: D:/Nokia_Interview_Prep/antigravity_server/Instruction/01_QUICK_START_CONNECT_NEW_APP.md
    """
    local_env = load_local_env()
    ep = (endpoint or "").strip()
    if not ep:
        ep = (
            os.getenv("ANTIGRAVITY_ENDPOINT")
            or os.getenv("ANTIGRAVITY_VIRTUAL_URL")
            or local_env.get("ANTIGRAVITY_ENDPOINT")
            or local_env.get("ANTIGRAVITY_VIRTUAL_URL")
            or ""
        ).strip()

    if not ep:
        slug = (
            pub_slug
            or os.getenv("ANTIGRAVITY_PUB_SLUG")
            or local_env.get("ANTIGRAVITY_PUB_SLUG")
            or DEFAULT_PUB_SLUG
        ).strip().lstrip("/")
        gw = (
            gateway_url
            or os.getenv("ANTIGRAVITY_GATEWAY_URL")
            or local_env.get("ANTIGRAVITY_GATEWAY_URL")
            or DEFAULT_GATEWAY_URL
        ).strip().rstrip("/")
        return f"{gw}/p/{slug}/v1/chat/completions"

    ep = ep.rstrip("/")
    if ep.endswith("/chat/completions"):
        return ep
    if ep.endswith("/v1"):
        return f"{ep}/chat/completions"
    return f"{ep}/v1/chat/completions"


def get_api_key(cli_key: Optional[str] = None) -> Optional[str]:
    """
    Resolves an optional Antigravity API key from CLI args, environment, or .env file.
    Note: Under the Virtual Middleware architecture, client secret keys are NOT required.
    """
    def is_valid_key(k: Optional[str]) -> bool:
        if not k:
            return False
        k = k.strip()
        return bool(k and k != "your_antigravity_api_key_here" and not k.startswith("your_"))

    if is_valid_key(cli_key):
        return cli_key.strip()

    # Check process env
    env_key = os.getenv("ANTIGRAVITY_APP_KEY") or os.getenv("AGY_API_KEY")
    if is_valid_key(env_key):
        return env_key.strip()

    # Check local .env file
    local_env = load_local_env()
    if is_valid_key(local_env.get("ANTIGRAVITY_APP_KEY")):
        return local_env["ANTIGRAVITY_APP_KEY"].strip()
    if is_valid_key(local_env.get("AGY_API_KEY")):
        return local_env["AGY_API_KEY"].strip()

    return None


# ===================================================================
# 2. Antigravity AI Advisor (Reading Order & Metadata)
# ===================================================================

def call_virtual_middleware_ai(
    prompt: str,
    endpoint_url: str,
    model: str = DEFAULT_MODEL
) -> Optional[List[Dict[str, Any]]]:
    """
    Calls the Antigravity Keyless Virtual Middleware Route.
    Architectural Principle: Zero Client Keys.
    Authorization is validated via the 128-bit slug in the URL path.
    Header 'Authorization: Bearer none' is transmitted.
    """
    user_prompt = (
        f"You are an expert comic book archivist and historian. For the comic run, character, or storyline '{prompt}', "
        "provide a canonical chronological reading order breakdown of the essential comic issues or runs.\n"
        "Return ONLY a valid JSON array of objects in this exact format:\n"
        "[\n"
        "  {\n"
        '    "title": "Exact Title of Run or Issue (e.g. House of X)",\n'
        '    "year": 2019,\n'
        '    "issue_num": 1,\n'
        '    "author": "Creative Team (Writer and Artist)",\n'
        '    "synopsis": "Concise 1-2 sentence plot and continuity summary",\n'
        '    "search_query": "Clean archive search keywords (e.g. House of X)"\n'
        "  }\n"
        "]\n"
        "Output ONLY the JSON array without any markdown conversational text."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "effort": "low",
        "stream": False
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer none"
    }

    try:
        req = urllib.request.Request(
            endpoint_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read().decode("utf-8", errors="replace"))
            content = data["choices"][0]["message"]["content"]
            return parse_ai_json_targets(content)
    except Exception:
        return None


def call_authenticated_gateway_ai(
    prompt: str,
    api_key: str,
    url: str,
    model: str = DEFAULT_MODEL
) -> Optional[List[Dict[str, Any]]]:
    """Fallback: Calls standard authenticated gateway with a secret Bearer key."""
    user_prompt = (
        f"You are an expert comic book archivist and historian. For the comic run, character, or storyline '{prompt}', "
        "provide a canonical chronological reading order breakdown of the essential comic issues or runs.\n"
        "Return ONLY a valid JSON array of objects in this exact format:\n"
        "[\n"
        "  {\n"
        '    "title": "Exact Title of Run or Issue (e.g. House of X)",\n'
        '    "year": 2019,\n'
        '    "issue_num": 1,\n'
        '    "author": "Creative Team (Writer and Artist)",\n'
        '    "synopsis": "Concise 1-2 sentence plot and continuity summary",\n'
        '    "search_query": "Clean archive search keywords (e.g. House of X)"\n'
        "  }\n"
        "]\n"
        "Output ONLY the JSON array without any markdown conversational text."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "effort": "low"
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read().decode("utf-8", errors="replace"))
            content = data["choices"][0]["message"]["content"]
            return parse_ai_json_targets(content)
    except Exception:
        return None


def call_gemini_direct_ai(
    prompt: str,
    api_key: str,
    model: str = DEFAULT_MODEL
) -> Optional[List[Dict[str, Any]]]:
    """Fallback: Calls Google Generative Language API directly if AIza key provided."""
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    active_model = model if model.startswith("gemini") else "gemini-2.5-flash"
    return call_authenticated_gateway_ai(prompt, api_key=api_key, url=url, model=active_model)


def call_agy_cli_advisor(prompt: str) -> Optional[List[Dict[str, Any]]]:
    """
    Invokes the local 'agy' CLI command to fetch structured reading order.
    """
    import subprocess
    cli_prompt = (
        f"You are a comic book archivist. For the comic run or title '{prompt}', "
        "provide a list of canonical issues in chronological reading order as a pure JSON array. "
        "Each object must have fields: 'title' (str), 'year' (int), 'issue_num' (int), "
        "'author' (str), 'synopsis' (str), 'search_query' (str). "
        "Output ONLY the JSON array without any other text or markdown wrapper."
    )

    try:
        result = subprocess.run(
            ["agy", "-p", cli_prompt, "--disable-slash-commands"],
            capture_output=True,
            text=True,
            timeout=45
        )
        if result.returncode == 0 and result.stdout.strip():
            return parse_ai_json_targets(result.stdout)
    except Exception:
        pass
    return None


def _normalize_targets(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    clean_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        clean_items.append({
            "title": item.get("title", "Unknown Title"),
            "year": int(item.get("year", 0)) if str(item.get("year", 0)).isdigit() else 0,
            "issue_num": item.get("issue_num", 0),
            "author": item.get("author", "Unknown Creator"),
            "synopsis": item.get("synopsis", ""),
            "search_query": item.get("search_query") or item.get("title", "")
        })
    return clean_items


def parse_ai_json_targets(content: str) -> List[Dict[str, Any]]:
    """Extracts JSON or markdown reading order list of targets from text content."""
    if not content:
        return []

    # 1. First attempt: Direct JSON or stripped markdown code fences
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()

    try:
        items = json.loads(stripped)
        if isinstance(items, list):
            return _normalize_targets(items)
    except Exception:
        pass

    # 2. Second attempt: Outermost brackets match [ ... ]
    start = content.find("[")
    end = content.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            items = json.loads(content[start:end + 1])
            if isinstance(items, list):
                return _normalize_targets(items)
        except Exception:
            pass

    # 3. Third attempt: Regex bracket matching with object detection
    json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
    if json_match:
        try:
            items = json.loads(json_match.group(0))
            if isinstance(items, list):
                return _normalize_targets(items)
        except Exception:
            pass

    # 4. Fallback: Markdown numbered list parsing (e.g. 1. **House of X** (2019))
    md_matches = re.findall(r'^\s*(\d+)\.\s+\*\*([^*]+)\*\*(.*)', content, re.MULTILINE)
    if not md_matches:
        md_matches = re.findall(r'^\s*(\d+)\.\s+([^\n\r]+)', content, re.MULTILINE)

    if md_matches:
        clean_items = []
        for match in md_matches[:16]:
            num_str = match[0]
            raw_title = match[1].strip()
            extra = match[2] if len(match) > 2 else ""
            clean_title = re.sub(r'[\(\[\{].*?[\)\]\}]', '', raw_title).strip().strip(':').strip()
            if any(bad in clean_title.lower() for bad in ["prologue", "foundation", "overview", "introduction", "timeline", "recommendation", "note"]):
                continue
            if not clean_title or len(clean_title) < 3:
                continue
            yr_match = re.search(r'\b(19\d{2}|20\d{2})\b', extra or raw_title)
            yr = int(yr_match.group(1)) if yr_match else 0
            clean_items.append({
                "title": clean_title,
                "year": yr,
                "issue_num": int(num_str) if num_str.isdigit() else 0,
                "author": "N/A",
                "synopsis": extra.strip()[:150],
                "search_query": clean_title
            })
        if clean_items:
            return clean_items

    return []


def fetch_comic_chronology_details(
    query: str,
    endpoint: Optional[str] = None,
    pub_slug: Optional[str] = None,
    api_key: Optional[str] = None,
    gateway_url: str = DEFAULT_GATEWAY_URL,
    model: str = DEFAULT_MODEL
) -> List[Dict[str, Any]]:
    """
    Fetches reading order from Antigravity Virtual Middleware, Gateway API, or local agy CLI.
    Priority:
      1. Safe Keyless Virtual Middleware Route (/p/{slug}/v1) [Zero Client Keys]
      2. Authenticated Gateway Route (/v1) if secret key explicitly provided
      3. Google Gemini Direct API if AIza key provided
      4. Local Antigravity 'agy' CLI
      5. Direct archive query fallback
    """
    print(f"\n[*] Consulting Antigravity AI Advisor on '{query}'...")

    # 1. Keyless Virtual Middleware Route (Zero Client Keys)
    virtual_url = resolve_virtual_middleware_url(endpoint=endpoint, pub_slug=pub_slug, gateway_url=gateway_url)
    clean_display = virtual_url.split("/chat/completions")[0]
    print(f"    -> Querying Antigravity Keyless Virtual Middleware at {clean_display}...")
    targets = call_virtual_middleware_ai(prompt=query, endpoint_url=virtual_url, model=model)
    if targets:
        print(f"    [✓] Received {len(targets)} canonical issue(s) from Antigravity Virtual Middleware.")
        return targets

    # 2. Authenticated Gateway Route (if secret key provided)
    if api_key and not api_key.startswith("AIza"):
        gw_completions_url = f"{gateway_url.rstrip('/')}/v1/chat/completions"
        print(f"    -> Querying Antigravity Gateway (API Key Auth) at {gw_completions_url}...")
        targets = call_authenticated_gateway_ai(prompt=query, api_key=api_key, url=gw_completions_url, model=model)
        if targets:
            print(f"    [✓] Received {len(targets)} canonical issue(s) from Antigravity Gateway.")
            return targets

    # 3. Google Gemini Direct API (if AIza key provided)
    if api_key and api_key.startswith("AIza"):
        print("    -> Querying Google Generative Language API directly...")
        targets = call_gemini_direct_ai(prompt=query, api_key=api_key, model=model)
        if targets:
            print(f"    [✓] Received {len(targets)} canonical issue(s) from Gemini API.")
            return targets

    # 4. Local Antigravity 'agy' CLI
    print("    -> Querying local Antigravity 'agy' CLI...")
    targets = call_agy_cli_advisor(query)
    if targets:
        print(f"    [✓] Received {len(targets)} canonical issue(s) from Antigravity CLI.")
        return targets

    # 5. Direct search fallback
    print("    [!] AI advisor offline. Proceeding with direct archive search for query.")
    return [{
        "title": query,
        "year": 0,
        "issue_num": 0,
        "author": "N/A",
        "synopsis": "Direct user search query",
        "search_query": query
    }]


# ===================================================================
# 3. Open Comic Archive Search & File Discovery
# ===================================================================

def sanitize_folder_name(name: str) -> str:
    """Removes invalid filesystem characters."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return re.sub(r'\s+', " ", clean)


def extract_issue_number(text: str) -> Optional[float]:
    """Extracts issue number from titles or filenames (e.g. #01, #404, 01 of 06, Issue 2)."""
    # Pattern 1: #01, #404, # 01
    m = re.search(r'#\s*(\d+(?:\.\d+)?)', text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    # Pattern 2: Issue 01, Issue 404
    m = re.search(r'\b(?:issue|iss|no)\.?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    # Pattern 3: (01 of 06), (01.04)
    m = re.search(r'\(#?\s*(\d+)\s*(?:of|\.|\/)\s*\d+\)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    # Pattern 4: - 01.cbz, _001.cbr
    m = re.search(r'[-_\s](\d{1,3})\.(?:cbz|cbr|pdf|zip)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    return None


def extract_year_from_text(text: str) -> Optional[int]:
    """Finds publication year like (1987) or 1987 in text."""
    m = re.search(r'\b(19\d\d|20\d\d)\b', text)
    if m:
        return int(m.group(1))
    return None


def search_archive_org(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Searches open comic archives on Archive.org."""
    clean_q = re.sub(r'Vol\.\s*\d+', '', query, flags=re.IGNORECASE)
    clean_q = re.sub(r'[#:\(\)\/]', ' ', clean_q).strip()
    words = clean_q.split()[:5]
    search_term = " ".join(words)
    encoded = urllib.parse.quote(search_term)

    url = (
        f"https://archive.org/advancedsearch.php?"
        f"q=mediatype:texts+AND+title:({encoded})+AND+(format:cbz+OR+format:cbr+OR+subject:comic+OR+subject:comics+OR+collection:comicbooksamy+OR+collection:comics_inbox+OR+description:comic)"
        f"&fl[]=identifier,title,downloads,year,description"
        f"&sort[]=downloads+desc&rows={max_results}&output=json"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "AntigravityComicChronology/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            data = json.loads(res.read().decode())
            docs = data.get("response", {}).get("docs", [])
            if docs:
                return docs
    except Exception:
        pass

    # Fallback to general title search
    url_fallback = (
        f"https://archive.org/advancedsearch.php?"
        f"q=mediatype:texts+AND+title:({encoded})"
        f"&fl[]=identifier,title,downloads,year,description"
        f"&sort[]=downloads+desc&rows={max_results}&output=json"
    )
    req = urllib.request.Request(url_fallback, headers={"User-Agent": "AntigravityComicChronology/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            data = json.loads(res.read().decode())
            return data.get("response", {}).get("docs", [])
    except Exception:
        return []


def get_archive_files_for_item(identifier: str) -> List[Dict[str, Any]]:
    """Fetches all valid downloadable comic files (.cbz, .cbr, .pdf, .zip) from an item."""
    meta_url = f"https://archive.org/metadata/{identifier}/files"
    req = urllib.request.Request(meta_url, headers={"User-Agent": "AntigravityComicChronology/3.0"})

    files_list = []
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            data = json.loads(res.read().decode())
            files = data.get("result", [])

            for f in files:
                name = f.get("name", "")
                ext = name.lower().split(".")[-1] if "." in name else ""
                if ext in ["cbz", "cbr", "pdf", "zip"]:
                    # Filter out non-comic archives or auxiliary derivative files
                    if any(bad in name.lower() for bad in ["_daisy", "_thumb", "_jp2.zip", "_text.pdf", "meta.xml", "files.xml"]):
                        continue
                    size_bytes = int(f.get("size", 0) or 0)
                    size_mb = round(size_bytes / (1024 * 1024), 2)
                    if size_mb < 0.5:
                        continue

                    files_list.append({
                        "name": name,
                        "format": ext.upper(),
                        "size_mb": size_mb,
                        "download_url": f"https://archive.org/download/{identifier}/{name}"
                    })
    except Exception:
        pass
    return files_list


def discover_available_comics(
    query: str,
    ai_targets: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Searches open comic archives for the run and individual issues,
    extracts files, associates metadata, and sorts chronologically.
    """
    print(f"\n[*] Searching open comic archives for available issues...")
    discovered = []
    seen_urls = set()
    seen_filenames = set()
    discovered_identifiers = set()
    best_by_group = {}

    # Collect search terms: overall query first, then clean AI target titles & search_queries
    search_queries = [query]
    for target in ai_targets:
        sq = target.get("search_query", "").strip()
        if sq and sq.lower() != query.lower() and sq not in search_queries:
            search_queries.append(sq)
        title = target.get("title", "")
        # Remove volume numbers, issue numbers, parentheses, subtitles after colon
        clean_title = re.sub(r'Vol\.\s*\d+|#\d+|\(.*?\)|:\s*.*', '', title).strip()
        parts = [p.strip() for p in clean_title.split("/") if p.strip()]
        for p in parts:
            if len(p) >= 3 and p.lower() != query.lower() and p not in search_queries:
                search_queries.append(p)

    for s_idx, q in enumerate(search_queries[:10], 1):
        print(f"    [{s_idx}/{min(len(search_queries), 10)}] Searching: '{q}'...")
        docs = search_archive_org(q, max_results=4)
        for doc in docs:
            ident = doc.get("identifier")
            if not ident or ident in discovered_identifiers:
                continue
            discovered_identifiers.add(ident)
            doc_title = doc.get("title", ident)
            doc_year = doc.get("year")
            if not doc_year:
                doc_year = extract_year_from_text(doc_title) or 0
            else:
                try:
                    doc_year = int(doc_year)
                except ValueError:
                    doc_year = 0

            # Get files for this item
            item_files = get_archive_files_for_item(ident)
            for f in item_files:
                if f["download_url"] in seen_urls:
                    continue
                seen_urls.add(f["download_url"])

                # De-duplicate by normalized filename
                norm_name = re.sub(r'[\s_\-]+', '_', f["name"].lower().strip())
                if norm_name in seen_filenames:
                    continue
                seen_filenames.add(norm_name)

                file_issue_num = extract_issue_number(f["name"]) or extract_issue_number(doc_title) or 0
                file_year = extract_year_from_text(f["name"]) or doc_year

                # Attempt to match with AI target metadata
                matched_target = None
                for target in ai_targets:
                    t_issue = target.get("issue_num", 0)
                    if t_issue and file_issue_num and int(t_issue) == int(file_issue_num):
                        matched_target = target
                        break

                if not matched_target and ai_targets:
                    # Match by name or default to first target
                    for target in ai_targets:
                        t_title = target.get("title", "").lower()
                        if any(w in f["name"].lower() for w in t_title.split()[:2]):
                            matched_target = target
                            break

                final_year = file_year or (matched_target.get("year", 0) if matched_target else 0)
                final_author = matched_target.get("author", "N/A") if matched_target else "N/A"
                final_synopsis = matched_target.get("synopsis", "") if matched_target else ""
                display_title = (
                    f"#{int(file_issue_num)}: {matched_target.get('title')}"
                    if matched_target and file_issue_num
                    else f.get("name")
                )
                # Format Prioritization: CBZ (1) > CBR (2) > ZIP (3) > PDF (4, Fallback)
                format_ranks = {"CBZ": 1, "CBR": 2, "ZIP": 3, "PDF": 4}
                file_fmt = f["format"].upper()
                fmt_rank = format_ranks.get(file_fmt, 99)

                clean_stem = re.sub(r'[\s_\-]+', '_', Path(f["name"]).stem.lower())
                clean_stem = re.sub(r'\([^\)]*\)', '', clean_stem).strip('_')
                if file_issue_num and file_issue_num > 0:
                    group_key = f"issue_{int(file_issue_num)}"
                else:
                    group_key = f"stem_{clean_stem}"

                item_entry = {
                    "filename": f["name"],
                    "display_title": display_title,
                    "format": file_fmt,
                    "fmt_rank": fmt_rank,
                    "size_mb": f["size_mb"],
                    "download_url": f["download_url"],
                    "year": final_year,
                    "issue_num": file_issue_num,
                    "author": final_author,
                    "synopsis": final_synopsis,
                    "archive_title": doc_title,
                    "identifier": ident,
                    "is_fallback_pdf": (file_fmt == "PDF")
                }

                # If we haven't seen this issue/stem yet, or new format has higher priority (lower rank)
                if group_key not in best_by_group:
                    best_by_group[group_key] = item_entry
                else:
                    existing_entry = best_by_group[group_key]
                    if fmt_rank < existing_entry["fmt_rank"]:
                        best_by_group[group_key] = item_entry

    discovered = list(best_by_group.values())

    # Sort in chronological order (Year ascending, Issue Number ascending)
    discovered.sort(key=lambda x: (
        x["year"] if x["year"] and x["year"] > 1900 else 9999,
        x["issue_num"] if x["issue_num"] else 9999,
        x["fmt_rank"],
        x["filename"].lower()
    ))

    # Determine recommended folder name
    target_years = [t.get("year", 0) for t in ai_targets if t.get("year", 0) and t.get("year", 0) >= 1930]
    first_year = target_years[0] if target_years else next((d["year"] for d in discovered if d["year"] and d["year"] >= 1930), None)
    year_tag = f" ({first_year})" if first_year else ""
    folder_name = sanitize_folder_name(f"{query.title()}{year_tag}")

    return discovered, folder_name


# ===================================================================
# 4. Interactive Selection & Approval Gate ("Click Yes")
# ===================================================================

def get_terminal_key() -> str:
    """Reads a single keypress from terminal across Windows, macOS, and Linux."""
    if os.name == "nt":
        import msvcrt
        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            key2 = msvcrt.getwch()
            if key2 == "H":
                return "UP"
            if key2 == "P":
                return "DOWN"
        if key == " ":
            return "SPACE"
        if key in ("\r", "\n"):
            return "ENTER"
        if key == "\x1b":
            return "ESC"
        return key.lower()
    else:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    if ch3 == "A":
                        return "UP"
                    if ch3 == "B":
                        return "DOWN"
                return "ESC"
            if ch == " ":
                return "SPACE"
            if ch in ("\r", "\n"):
                return "ENTER"
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def clear_screen():
    """Clears terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def interactive_checkbox_selector(items: List[Dict[str, Any]], default_folder: str) -> List[Dict[str, Any]]:
    """
    Renders an interactive TUI selector with checkboxes:
      ↑/↓    : Move cursor
      SPACE  : Tick / Untick
      A      : Select All
      N      : Select None
      ENTER  : Confirm Selection
      Q      : Cancel / Exit
    """
    if not items:
        return []

    # Default: select all
    selected = [True] * len(items)
    cursor = 0

    # Fallback to plain prompt if not a real interactive terminal
    if not sys.stdin.isatty():
        return plain_text_selector(items)

    while True:
        clear_screen()
        print("═" * 78)
        print("  📚 SELECT COMICS TO DOWNLOAD (CHRONOLOGICAL ORDER)")
        print("═" * 78)
        print("  [↑ / ↓] Move Cursor   |  [SPACE] Toggle [x]/[ ]  |  [A] Select All")
        print("  [N] Deselect None     |  [ENTER] Confirm (Yes)   |  [Q] Cancel")
        print("─" * 78)

        total_selected = sum(selected)
        total_size_mb = sum(items[i]["size_mb"] for i in range(len(items)) if selected[i])
        print(f"  Selected: {total_selected} of {len(items)} comics | Total Size: {total_size_mb:.1f} MB")
        print("─" * 78)

        # Show visible window of items if list is long
        max_rows = 15
        start_idx = max(0, min(cursor - max_rows // 2, len(items) - max_rows))
        end_idx = min(len(items), start_idx + max_rows)

        if start_idx > 0:
            print(f"  ... ({start_idx} earlier items above) ...")

        for i in range(start_idx, end_idx):
            item = items[i]
            pointer = "▶" if i == cursor else " "
            checkbox = "[x]" if selected[i] else "[ ]"
            year_str = f"[{item['year']}] " if item["year"] else ""
            num_str = f"#{int(item['issue_num']):02d} " if item["issue_num"] else ""
            size_fmt = f"[{item['format']} | {item['size_mb']:5.1f} MB]"
            
            line = f"  {pointer} {checkbox} {i+1:2d}. {year_str}{num_str}{item['filename'][:40]} {size_fmt}"
            print(line)

        if end_idx < len(items):
            print(f"  ... ({len(items) - end_idx} more items below) ...")

        print("═" * 78)
        print("  Press ENTER when done to approve and proceed with download.")

        key = get_terminal_key()

        if key == "UP":
            cursor = (cursor - 1) % len(items)
        elif key == "DOWN":
            cursor = (cursor + 1) % len(items)
        elif key == "SPACE":
            selected[cursor] = not selected[cursor]
        elif key == "a":
            selected = [True] * len(items)
        elif key == "n":
            selected = [False] * len(items)
        elif key in ("q", "esc"):
            print("\n[-] Selection cancelled by user.")
            return []
        elif key == "ENTER":
            if not any(selected):
                print("\n  [!] No comics selected. Press SPACE on an item to select it, or A for all.")
                time.sleep(1.2)
                continue
            return [items[i] for i in range(len(items)) if selected[i]]


def plain_text_selector(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fallback selector for environments without raw tty capability."""
    print("\n" + "═" * 78)
    print("  📚 AVAILABLE COMICS (CHRONOLOGICAL ORDER)")
    print("═" * 78)
    for idx, item in enumerate(items, 1):
        year_str = f"[{item['year']}] " if item["year"] else ""
        num_str = f"#{int(item['issue_num']):02d} " if item["issue_num"] else ""
        print(f"  {idx:2d}. {year_str}{num_str}{item['filename']} [{item['format']} | {item['size_mb']} MB]")
    print("═" * 78)
    print("  Enter item numbers to download (e.g. '1, 2, 4-6' or 'all'): ")
    try:
        choice = input("  Selection: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return []

    if choice in ("", "all"):
        return items
    if choice in ("none", "q", "quit"):
        return []

    selected_indices = set()
    parts = choice.split(",")
    for p in parts:
        p = p.strip()
        if "-" in p:
            sub = p.split("-", 1)
            try:
                start, end = int(sub[0]), int(sub[1])
                for x in range(start, end + 1):
                    if 1 <= x <= len(items):
                        selected_indices.add(x - 1)
            except ValueError:
                pass
        else:
            try:
                val = int(p)
                if 1 <= val <= len(items):
                    selected_indices.add(val - 1)
            except ValueError:
                pass

    return [items[i] for i in sorted(selected_indices)]


def confirm_approval_gate(selected_files: List[Dict[str, Any]], folder_name: str) -> bool:
    """
    Final approval gate: Displays selected list, destination directory,
    and asks user to confirm ('Click Yes' / [y/n]).
    """
    clear_screen()
    print("\n" + "═" * 78)
    print("  ✅ DOWNLOAD CONFIRMATION & APPROVAL GATE")
    print("═" * 78)
    target_path = DOWNLOADS_ROOT / folder_name
    total_mb = sum(f["size_mb"] for f in selected_files)

    print(f"  Target Run Folder : {target_path}")
    print(f"  Comics Selected   : {len(selected_files)} issue(s)")
    print(f"  Total Download    : {total_mb:.1f} MB")
    print("─" * 78)
    print("  Selected Issues to Download:")
    for i, f in enumerate(selected_files[:10], 1):
        year_tag = f"({f['year']}) " if f["year"] else ""
        print(f"    {i:2d}. {year_tag}{f['filename']} ({f['size_mb']} MB)")
    if len(selected_files) > 10:
        print(f"    ... and {len(selected_files) - 10} more issue(s)")
    print("═" * 78)

    prompt = "  Ready to create folder and download all selected comics? [Y/n] (Click Yes): "
    try:
        decision = input(prompt).strip().lower()
        if decision in ("", "y", "yes", "true", "1"):
            return True
        else:
            print("\n[-] Download cancelled by user.")
            return False
    except (EOFError, KeyboardInterrupt):
        print("\n[-] Cancelled.")
        return False


# ===================================================================
# 5. Streaming Downloader & Progress Bar
# ===================================================================

def download_file_with_progress(url: str, dest_path: Path) -> bool:
    """Downloads a file with an active ASCII progress bar."""
    if dest_path.exists() and dest_path.stat().st_size > 1000:
        print(f"  [✓] File already exists: {dest_path.name}")
        return True

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "AntigravityComicChronology/3.0"})

    try:
        with urllib.request.urlopen(req, timeout=40) as res:
            total_bytes = int(res.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 64 * 1024
            start_time = time.time()

            with open(dest_path, "wb") as f:
                while True:
                    chunk = res.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_bytes > 0:
                        pct = int((downloaded / total_bytes) * 100)
                        done_mb = downloaded / (1024 * 1024)
                        total_mb = total_bytes / (1024 * 1024)
                        speed = done_mb / max(0.1, (time.time() - start_time))
                        bar_len = 20
                        filled = int(bar_len * downloaded // total_bytes)
                        bar = "#" * filled + "-" * (bar_len - filled)
                        sys.stdout.write(f"\r    [{bar}] {pct:3d}% | {done_mb:5.1f}/{total_mb:5.1f} MB | {speed:4.1f} MB/s")
                        sys.stdout.flush()

            sys.stdout.write("\n")
            return True
    except Exception as e:
        print(f"\n    [!] Download failed: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return False


def execute_bulk_downloads(selected_files: List[Dict[str, Any]], folder_name: str):
    """Creates the target folder and downloads all approved comics."""
    target_dir = DOWNLOADS_ROOT / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "═" * 78)
    print(f"  🚀 STARTING DOWNLOADS TO: {target_dir}")
    print("═" * 78)

    successful = 0
    failed = []

    for idx, item in enumerate(selected_files, 1):
        filename = item["filename"]
        dest = target_dir / filename
        print(f"\n  [{idx}/{len(selected_files)}] Downloading: {filename} ({item['size_mb']} MB)")
        ok = download_file_with_progress(item["download_url"], dest)
        if ok:
            successful += 1
        else:
            failed.append(filename)

    print("\n" + "═" * 78)
    print("  🎉 DOWNLOAD BATCH COMPLETE")
    print("═" * 78)
    print(f"  Saved to Directory: {target_dir}")
    print(f"  Successful        : {successful} / {len(selected_files)}")
    if failed:
        print(f"  Failed            : {len(failed)}")
        for f in failed:
            print(f"    - {f}")
    print("═" * 78 + "\n")


# ===================================================================
# 6. Main Orchestrator
# ===================================================================

def run_comic_downloader(
    query: Optional[str] = None,
    endpoint: Optional[str] = None,
    pub_slug: Optional[str] = None,
    api_key: Optional[str] = None,
    gateway_url: str = DEFAULT_GATEWAY_URL,
    model: str = DEFAULT_MODEL
):
    """Complete user workflow for Antigravity Comic Chronology Downloader."""
    print("═" * 78)
    print("        📚 Antigravity Comic Chronology Finder & Downloader")
    print("═" * 78)

    # 1. Resolve User Query
    if not query:
        try:
            query = input("\n  Enter comic name, comic run, or storyline: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[-] Exiting.")
            return

    if not query:
        print("[-] Empty query. Exiting.")
        return

    # 2. Antigravity AI Advisor fetches reading order & canonical issue details
    resolved_key = get_api_key(api_key)
    ai_targets = fetch_comic_chronology_details(
        query=query,
        endpoint=endpoint,
        pub_slug=pub_slug,
        api_key=resolved_key,
        gateway_url=gateway_url,
        model=model
    )

    # 3. Search open archives & sort chronologically
    available_comics, folder_name = discover_available_comics(query, ai_targets)

    if not available_comics:
        print(f"\n[-] No downloadable comic files (.cbz, .cbr, .pdf) found for '{query}'.")
        print("    Try adjusting the search query or using a specific character/issue name.\n")
        return

    # 4. Interactive Selection
    selected_comics = interactive_checkbox_selector(available_comics, folder_name)
    if not selected_comics:
        print("[-] No comics selected for download.\n")
        return

    # 5. User Approval Confirmation ("Click Yes")
    approved = confirm_approval_gate(selected_comics, folder_name)
    if not approved:
        return

    # 6. Create Folder and Download
    execute_bulk_downloads(selected_comics, folder_name)


def main():
    parser = argparse.ArgumentParser(
        description="Antigravity Comic Chronology Finder & Bulk Downloader (Virtual Middleware Enabled)"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Comic name, run, or storyline (e.g. 'Batman Year One', 'House of X', 'X men Krakoa era')"
    )
    parser.add_argument(
        "--endpoint",
        dest="endpoint",
        default=None,
        help="Antigravity Safe Keyless Virtual Middleware endpoint URL"
    )
    parser.add_argument(
        "--pub-slug",
        dest="pub_slug",
        default=None,
        help="Antigravity 128-bit public slug for keyless middleware (e.g. pub_b93935784aff3f67d55d904e7e43f30f)"
    )
    parser.add_argument(
        "--key",
        dest="api_key",
        default=None,
        help="Optional secret API key (for legacy gateway route / Gemini fallback)"
    )
    parser.add_argument(
        "--gateway",
        dest="gateway_url",
        default=DEFAULT_GATEWAY_URL,
        help="Antigravity Gateway URL (default: http://127.0.0.1:8000)"
    )
    parser.add_argument(
        "--model",
        dest="model",
        default=DEFAULT_MODEL,
        help="Model name for Antigravity AI Advisor (default: gemini-2.5-flash)"
    )

    args = parser.parse_args()
    run_comic_downloader(
        query=args.query,
        endpoint=args.endpoint,
        pub_slug=args.pub_slug,
        api_key=args.api_key,
        gateway_url=args.gateway_url,
        model=args.model
    )


if __name__ == "__main__":
    main()
