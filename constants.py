# ============================================================
#  constants.py  —  Apex PlayerCard Bot
# ============================================================

# ------------------------------------------------------------------
# ROLE / ARCHETYPE ASSIGNMENTS
# ------------------------------------------------------------------
ROLE_MAP = {
    "ANCHOR": [
        "Caustic", "Wattson", "Rampart", "Catalyst",
        "Gibraltar", "Newcastle", "Vantage",
    ],
    "FRAGGER": [
        "Bangalore", "Revenant", "Fuse", "Mad Maggie",
        "Ballistic", "Wraith", "Octane", "Horizon", "Ash",
    ],
    "REFRAG": [
        "Pathfinder", "Alter", "Valkyrie", "Seer", "Crypto",
    ],
    "SUPPORT": [
        "Lifeline", "Mirage", "Loba", "Conduit",
    ],
}

# Reverse lookup: legend name → role
LEGEND_TO_ROLE: dict[str, str] = {}
for role, legends in ROLE_MAP.items():
    for legend in legends:
        LEGEND_TO_ROLE[legend.lower()] = role


# ------------------------------------------------------------------
# RARITY SYSTEM
# ------------------------------------------------------------------
RARITIES = [
    {
        "name": "MYTHIC",
        "weight": 0.010,
        "frame_color": (180, 20, 20),
        "accent_color": (255, 60, 60),
        "text_color": (255, 200, 200),
        "glow": True,
        "pulse": True,
        "foil": False,
    },
    {
        "name": "HOLO",
        "weight": 0.005,
        "frame_color": (200, 200, 255),
        "accent_color": (180, 100, 255),
        "text_color": (255, 255, 255),
        "glow": True,
        "pulse": False,
        "foil": True,          # Full iridescent rainbow overlay
    },
    {
        "name": "LEGENDARY",
        "weight": 0.085,
        "frame_color": (180, 140, 20),
        "accent_color": (255, 215, 0),
        "text_color": (255, 240, 180),
        "glow": True,
        "pulse": False,
        "foil": False,
    },
    {
        "name": "EPIC",
        "weight": 0.150,
        "frame_color": (100, 30, 160),
        "accent_color": (180, 80, 255),
        "text_color": (220, 180, 255),
        "glow": False,
        "pulse": False,
        "foil": False,
    },
    {
        "name": "RARE",
        "weight": 0.250,
        "frame_color": (20, 80, 180),
        "accent_color": (60, 140, 255),
        "text_color": (180, 210, 255),
        "glow": False,
        "pulse": False,
        "foil": False,
    },
    {
        "name": "COMMON",
        "weight": 0.500,
        "frame_color": (80, 80, 90),
        "accent_color": (150, 150, 160),
        "text_color": (210, 210, 215),
        "glow": False,
        "pulse": False,
        "foil": False,
    },
]

RARITY_NAMES   = [r["name"]   for r in RARITIES]
RARITY_WEIGHTS = [r["weight"] for r in RARITIES]


# ------------------------------------------------------------------
# OVR CALCULATION WEIGHTS  (must sum to 1.0)
# Ranked: AVG DMG > Assists > Top 5 > K/D > Survival Time
# ------------------------------------------------------------------
OVR_WEIGHTS = {
    "avg_dmg":      0.38,
    "assists":      0.25,
    "total_kills":  0.18,
    "kd":           0.12,
    "survival_time": 0.07,
}

# Benchmark ceilings — recalibrated for scrim players
OVR_CEILINGS = {
    "avg_dmg":       850,    # 800+ is excellent in scrims
    "assists":       1.5,    # avg assists per game
    "total_kills":   1500,   # total kills across all tracked games
    "kd":            1.2,    # sub-1.5 KD is common in scrims
    "survival_time": 15.0,   # average minutes survived
}


# ------------------------------------------------------------------
# LEGEND ART — wiki scrape sources
# Key: lowercase legend name  |  Value: Apex wiki image page URL
# ------------------------------------------------------------------
LEGEND_ART_URLS = {
    "bangalore":   "https://static.wikia.nocookie.net/apexlegends/images/b/b9/Bangalore_artwork.png",
    "bloodhound":  "https://static.wikia.nocookie.net/apexlegends/images/7/76/Bloodhound_artwork.png",
    "caustic":     "https://static.wikia.nocookie.net/apexlegends/images/9/9f/Caustic_artwork.png",
    "crypto":      "https://static.wikia.nocookie.net/apexlegends/images/1/17/Crypto_artwork.png",
    "fuse":        "https://static.wikia.nocookie.net/apexlegends/images/1/1c/Fuse_artwork.png",
    "gibraltar":   "https://static.wikia.nocookie.net/apexlegends/images/4/4b/Gibraltar_artwork.png",
    "horizon":     "https://static.wikia.nocookie.net/apexlegends/images/8/88/Horizon_artwork.png",
    "lifeline":    "https://static.wikia.nocookie.net/apexlegends/images/4/43/Lifeline_artwork.png",
    "loba":        "https://static.wikia.nocookie.net/apexlegends/images/a/a0/Loba_artwork.png",
    "mirage":      "https://static.wikia.nocookie.net/apexlegends/images/2/22/Mirage_artwork.png",
    "newcastle":   "https://static.wikia.nocookie.net/apexlegends/images/d/d2/Newcastle_artwork.png",
    "octane":      "https://static.wikia.nocookie.net/apexlegends/images/c/c9/Octane_artwork.png",
    "pathfinder":  "https://static.wikia.nocookie.net/apexlegends/images/e/ef/Pathfinder_artwork.png",
    "rampart":     "https://static.wikia.nocookie.net/apexlegends/images/a/a3/Rampart_artwork.png",
    "revenant":    "https://static.wikia.nocookie.net/apexlegends/images/6/60/Revenant_artwork.png",
    "seer":        "https://static.wikia.nocookie.net/apexlegends/images/7/71/Seer_artwork.png",
    "valkyrie":    "https://static.wikia.nocookie.net/apexlegends/images/5/52/Valkyrie_artwork.png",
    "vantage":     "https://static.wikia.nocookie.net/apexlegends/images/e/e1/Vantage_artwork.png",
    "wattson":     "https://static.wikia.nocookie.net/apexlegends/images/3/3f/Wattson_artwork.png",
    "wraith":      "https://static.wikia.nocookie.net/apexlegends/images/a/ac/Wraith_artwork.png",
    "ash":         "https://static.wikia.nocookie.net/apexlegends/images/6/65/Ash_artwork.png",
    "mad maggie":  "https://static.wikia.nocookie.net/apexlegends/images/1/14/Mad_Maggie_artwork.png",
    "ballistic":   "https://static.wikia.nocookie.net/apexlegends/images/f/f7/Ballistic_artwork.png",
    "conduit":     "https://static.wikia.nocookie.net/apexlegends/images/c/cb/Conduit_artwork.png",
    "alter":       "https://static.wikia.nocookie.net/apexlegends/images/0/09/Alter_artwork.png",
    "catalyst":    "https://static.wikia.nocookie.net/apexlegends/images/a/a5/Catalyst_artwork.png",
}

# Card dimensions
CARD_W = 480
CARD_H = 720

# Font paths (relative to project root)
FONT_DIR = "assets/fonts"

# Legend art cache dir
LEGEND_CACHE_DIR = "cache/legends"
