#!/usr/bin/env python3
"""
Standalone scraper worker — run as subprocess.
Prints JSON result to stdout.
Usage: python scraper_worker.py <url>
"""
import sys
import re
import json

KNOWN_LEGENDS = [
    "bangalore", "bloodhound", "caustic", "crypto", "fuse",
    "gibraltar", "horizon", "lifeline", "loba", "mirage",
    "newcastle", "octane", "pathfinder", "rampart", "revenant",
    "seer", "valkyrie", "vantage", "wattson", "wraith", "ash",
    "mad maggie", "ballistic", "conduit", "alter", "catalyst", "sparrow",
]

def _clean_float(text):
    try:
        cleaned = re.sub(r"[^\d.]", "", text.strip())
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0

def _parse_survival(text):
    text = text.strip().lower()
    m = re.search(r"(\d+)m\s*(\d+)s", text)
    if m: return int(m.group(1)) + int(m.group(2)) / 60
    m = re.match(r"([\d.]+)\s*m", text)
    if m: return float(m.group(1))
    return 0.0

def _extract_username(url):
    m = re.search(r"/player/\d+\.([^/]+)", url)
    if m: return m.group(1).replace("_", " ")
    return "Unknown"

def main():
    url = sys.argv[1]
    if not url.endswith("/overview"):
        url += "/overview"

    username = _extract_username(url)
    avg_dmg = kd = assists = total_kills = total_games = survival_time = 0.0
    most_played_legend = "Wraith"

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-setuid-sandbox",
                  "--disable-dev-shm-usage","--disable-gpu"]
        )
        page = browser.new_page()
        page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}", lambda r: r.abort())
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        text = page.evaluate("() => document.body.innerText")
        browser.close()

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
        if line.lower() == "overview" and i > 0:
            username = lines[i-1]
            break

    for i, line in enumerate(lines):
        if "featured legends" in line.lower():
            for j in range(i+1, min(i+5, len(lines))):
                if lines[j].strip().lower() in KNOWN_LEGENDS:
                    most_played_legend = lines[j].strip().title()
                    break
            break

    for i, line in enumerate(lines):
        if "avg. damage" in line.lower() or "avg damage" in line.lower():
            for j in range(i+1, min(i+3, len(lines))):
                val = _clean_float(lines[j])
                if val > 0:
                    avg_dmg = val
                    break
            break

    for line in lines:
        lower = line.lower()
        if lower.startswith("assists"):
            parts = re.split(r"\s{2,}|\t", line)
            if len(parts) >= 3: assists = _clean_float(parts[2])
            elif len(parts) == 2: assists = _clean_float(parts[1])
        elif lower.startswith("kills"):
            parts = re.split(r"\s{2,}|\t", line)
            if len(parts) >= 2: total_kills = _clean_float(parts[1])
        elif lower.startswith("totalgames") or lower.startswith("total games"):
            parts = re.split(r"\s{2,}|\t", line)
            if len(parts) >= 2: total_games = _clean_float(parts[1])
        elif lower.startswith("time"):
            parts = re.split(r"\s{2,}|\t", line)
            if len(parts) >= 3: survival_time = _parse_survival(parts[-1])
            elif len(parts) == 2: survival_time = _parse_survival(parts[1])

    if total_games > 0 and total_kills > 0:
        kd = round(total_kills / total_games, 2)

    print(json.dumps({
        "username": username,
        "avg_dmg": round(avg_dmg, 1),
        "kd": round(kd, 2),
        "assists": round(assists, 2),
        "total_kills": int(total_kills),
        "survival_time": round(survival_time, 1),
        "most_played_legend": most_played_legend,
    }))

if __name__ == "__main__":
    main()
