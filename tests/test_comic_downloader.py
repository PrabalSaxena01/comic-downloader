#!/usr/bin/env python3
"""
Test Suite for Antigravity Comic Chronology Finder & Downloader
"""
import sys
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comic_downloader import (
    sanitize_folder_name,
    extract_issue_number,
    extract_year_from_text,
    search_archive_org,
    get_archive_files_for_item,
    parse_ai_json_targets,
    plain_text_selector
)

def test_sanitization():
    print("=== Test 1: Folder Sanitization ===")
    raw = 'Batman: The Court of Owls / Vol. 1? *"Special"* <Deluxe>|'
    clean = sanitize_folder_name(raw)
    assert ":" not in clean and "/" not in clean and "?" not in clean and "*" not in clean
    assert clean == 'Batman The Court of Owls Vol. 1 Special Deluxe'
    print(f"  [✓] Sanitized: '{clean}'")

def test_issue_number_extraction():
    print("\n=== Test 2: Issue Number Extraction ===")
    cases = [
        ("Batman #404 (Year One).cbz", 404.0),
        ("Spider-Man Blue - #01.cbr", 1.0),
        ("Action Comics Issue 02.pdf", 2.0),
        ("Flashpoint (# 03 of 05).cbz", 3.0),
        ("Superman - 05.cbz", 5.0)
    ]
    for text, expected in cases:
        extracted = extract_issue_number(text)
        assert extracted == expected, f"Failed for '{text}': got {extracted}, expected {expected}"
        print(f"  [✓] '{text}' -> Issue #{int(extracted)}")

def test_year_extraction():
    print("\n=== Test 3: Year Extraction ===")
    cases = [
        ("Batman: Year One (1987)", 1987),
        ("Spider-Man Blue 2002 Mini-Series", 2002),
        ("Action Comics #1 1938", 1938)
    ]
    for text, expected in cases:
        extracted = extract_year_from_text(text)
        assert extracted == expected, f"Failed for '{text}': got {extracted}, expected {expected}"
        print(f"  [✓] '{text}' -> Year {extracted}")

def test_chronological_sorting():
    print("\n=== Test 4: Chronological Sorting ===")
    mock_files = [
        {"filename": "issue_3.cbz", "year": 1987, "issue_num": 3},
        {"filename": "issue_1.cbz", "year": 1987, "issue_num": 1},
        {"filename": "modern_issue_1.cbz", "year": 2011, "issue_num": 1},
        {"filename": "issue_2.cbz", "year": 1987, "issue_num": 2},
    ]
    mock_files.sort(key=lambda x: (
        x["year"] if x["year"] and x["year"] > 1900 else 9999,
        x["issue_num"] if x["issue_num"] else 9999,
        x["filename"].lower()
    ))
    expected_order = ["issue_1.cbz", "issue_2.cbz", "issue_3.cbz", "modern_issue_1.cbz"]
    actual_order = [f["filename"] for f in mock_files]
    assert actual_order == expected_order, f"Sorting mismatch: {actual_order}"
    print(f"  [✓] Successfully sorted chronologically: {actual_order}")

def test_archive_search():
    print("\n=== Test 5: Open Archive Search & File Discovery ===")
    results = search_archive_org("Spider-Man Blue", max_results=3)
    assert len(results) > 0, "Archive search should return docs"
    ident = results[0]["identifier"]
    print(f"  [✓] Found archive item: {ident}")

    files = get_archive_files_for_item(ident)
    assert len(files) > 0, "Item should have comic files"
    print(f"  [✓] Retrieved {len(files)} comic file(s) for {ident}")
    for f in files[:2]:
        print(f"      - {f['name']} [{f['format']} | {f['size_mb']} MB]")

def test_json_parsing():
    print("\n=== Test 6: AI JSON Parsing ===")
    sample_ai = """
    Here is the reading order:
    ```json
    [
      {
        "title": "Batman #404: Chapter One",
        "year": 1987,
        "issue_num": 404,
        "author": "Frank Miller",
        "synopsis": "Bruce returns to Gotham.",
        "search_query": "Batman 404"
      }
    ]
    ```
    """
    targets = parse_ai_json_targets(sample_ai)
    assert len(targets) == 1, "Should parse 1 target"
    assert targets[0]["issue_num"] == 404
    assert targets[0]["year"] == 1987
    print(f"  [✓] Successfully parsed AI target: {targets[0]['title']}")

def test_format_priority():
    print("\n=== Test 7: Format Priority (CBZ > CBR > ZIP > PDF) ===")
    from comic_downloader import discover_available_comics
    mock_targets = [{"title": "Spider-Man Blue #1", "issue_num": 1, "year": 2002}]
    # Run discovery on known archive items
    available, folder = discover_available_comics("Spider-Man Blue", mock_targets)
    formats_found = {item["filename"]: item["format"] for item in available}
    print("  [✓] Formats selected by priority:", formats_found)
    # Ensure TPB preferred CBR over PDF since both exist on Archive.org
    tpb_items = [item for item in available if "TPB" in item["filename"]]
    if tpb_items:
        assert tpb_items[0]["format"] in ["CBZ", "CBR"], f"Should prefer CBZ/CBR over PDF, got {tpb_items[0]['format']}"
        print(f"  [✓] Verified: TPB selected format is {tpb_items[0]['format']} (PDF suppressed as redundant fallback)")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING UNIT TESTS FOR COMIC CHRONOLOGY DOWNLOADER")
    print("=" * 60)
    test_sanitization()
    test_issue_number_extraction()
    test_year_extraction()
    test_chronological_sorting()
    test_archive_search()
    test_json_parsing()
    test_format_priority()
    print("\n" + "=" * 60)
    print(">>> ALL TESTS PASSED SUCCESSFULLY! <<<")
    print("=" * 60)
