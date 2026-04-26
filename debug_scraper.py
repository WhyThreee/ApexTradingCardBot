import asyncio
import sys
sys.path.insert(0, '.')
from scraper import scrape_player

URL = "https://overstat.gg/player/2584.ColoHockey_/overview"

async def debug():
    print("Running scraper...")
    result = await scrape_player(URL)
    print("\n===== SCRAPER OUTPUT =====")
    for k, v in result.items():
        print(f"  {k}: {v}")

asyncio.run(debug())
