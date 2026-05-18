# ============================================================
#  card_generator.py  —  Apex PlayerCard Bot  (v9 - Template)
# ============================================================

import io, os, math, random, logging, urllib.request, json
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image, ImageDraw, ImageFont

from constants import LEGEND_TO_ROLE, RARITIES, RARITY_WEIGHTS, LEGEND_ART_URLS

logger = logging.getLogger(__name__)
FONT_DIR     = "assets/fonts"
TEMPLATE_DIR = "assets/templates"

# Style 1 templates
RARITY_TEMPLATES_S1 = {
    "COMMON":    "Blue_Style 1.png",
    "RARE":      "Blue_Style 1.png",
    "EPIC":      "Purple_Style 1.png",
    "LEGENDARY": "Gold_Style 1.png",
    "MYTHIC":    "Red_Style 1.png",
    "HOLO":      "Holo_Style 1.png",
}

# Style 2 templates
RARITY_TEMPLATES_S2 = {
    "COMMON":    "Blue_Style 2.png",
    "RARE":      "Blue_Style 2.png",
    "EPIC":      "Purple_Style 2.png",
    "LEGENDARY": "Gold_Style 2.png",
    "MYTHIC":    "Red_Style 2.png",
    "HOLO":      "Holo_Style 2.png",
}

# Style 3 templates
RARITY_TEMPLATES_S3 = {
    "COMMON":    "Blue_Style 3.png",
    "RARE":      "Blue_Style 3.png",
    "EPIC":      "Purple_Style 3.png",
    "LEGENDARY": "Gold_Style 3.png",
    "MYTHIC":    "Red_Style 3.png",
    "HOLO":      "Holo_Style 3.png",
}

# Keep default for backwards compat
RARITY_TEMPLATES = RARITY_TEMPLATES_S1

# Style 1 zones (918x1152)
ZONES_S1 = {
    "art_box":      (321,  92,  807,  603),
    "ovr":          ( 95,  54,  274,  198),
    "role":         ( 96, 202,  274,  247),
    "pfp":          (416, 610,  509,  703),
    "name":         ( 75, 710,  845,  858),
    "stat_avgdmg":  (107, 912,  239,  969),
    "stat_kd":      (253, 912,  385,  969),
    "stat_ast":     (399, 912,  529,  969),
    "stat_kills":   (544, 912,  677,  969),
    "stat_srt":     (692, 912,  816,  969),
}

# Style 2 zones (755x1072)
ZONES_S2 = {
    "art_box":      (305, 216,  618,  552),
    "ovr":          (118, 147,  248,  252),
    "role":         (120, 259,  248,  319),
    "pfp":          (111, 433,  254,  572),
    "name":         ( 90, 601,  665,  670),
    "stat_avgdmg":  (102, 694,  262,  763),
    "stat_kd":      (293, 694,  448,  763),
    "stat_ast":     (485, 694,  644,  763),
    "stat_kills":   (185, 830,  342,  897),
    "stat_srt":     (395, 830,  553,  897),
}

# Style 3 zones (896x1184)
ZONES_S3 = {
    "art_box":      (313, 129, 798, 574),
    "ovr":          (104, 121, 252, 235),
    "role":         (106, 239, 251, 293),
    "pfp":          (422, 624, 493, 695),
    "name":         (229, 718, 687, 780),
    "stat_avgdmg":  (105, 860, 220, 928),
    "stat_kd":      (232, 860, 351, 928),
    "stat_ast":     (371, 860, 487, 928),
    "stat_kills":   (499, 860, 636, 928),
    "stat_srt":     (654, 860, 812, 928),
}

# Logo zones per style (where server logo gets pasted)
LOGO_ZONES = {
    1: (136,  985, 453, 1099),  # Style 1 - bottom left
    2: (290,   72, 430,  207),  # Style 2 - top center (moved up 13px)
    3: ( 91,  963, 246, 1091),  # Style 3 - bottom left
}

# Server logo config — guild_id -> logo file path
SERVER_LOGOS = {
    1196223607655899187: "assets/logos/VESA_White.png",  # TESTING SERVER
    1292412338749837383: "assets/logos/VESA_White.png",
}

# Default zones (Style 1)
ZONES = ZONES_S1


def _font(size):
    """Load best available font — works on Windows and Linux/Railway."""
    candidates = [
        # Bundled font (works everywhere including Railway)
        os.path.join(FONT_DIR, "BebasNeue-Regular.ttf"),
        # Windows fonts
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        # Linux fonts (Railway)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    # Last resort - scale up default font
    return ImageFont.load_default()


def roll_rarity():
    return random.choices(RARITIES, weights=RARITY_WEIGHTS, k=1)[0]


def _load_template(rarity_name: str, templates: dict = None) -> Image.Image:
    if templates is None: templates = RARITY_TEMPLATES_S1
    fname = templates.get(rarity_name, list(templates.values())[0])
    for tdir in [TEMPLATE_DIR, "/mnt/user-data/uploads"]:
        tpath = Path(tdir) / fname
        if tpath.exists():
            return Image.open(tpath).convert("RGBA")
    raise FileNotFoundError(f"Template not found: {fname}")


def _get_wiki_art_url(legend_name):
    title = legend_name.replace(" ", "_").title()
    try:
        api = (f"https://apexlegends.fandom.com/api.php?action=query"
               f"&titles={title}&prop=pageimages&format=json&pithumbsize=900")
        req = urllib.request.Request(api, headers={"User-Agent": "ApexCardBot/2.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            for page in data.get("query", {}).get("pages", {}).values():
                t = page.get("thumbnail", {}).get("source")
                if t: return t
    except: pass
    return LEGEND_ART_URLS.get(legend_name.lower())


async def _fetch(url):
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"}) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.content
    except: return None


async def get_legend_image(legend_name):
    # 1. Local assets — try multiple case variants
    key = legend_name.lower().replace(" ", "_")
    key_title = legend_name.title().replace(" ", "_")
    
    for name_variant in [key, key_title, legend_name.replace(" ", "_")]:
        for ext in ("png", "webp", "jpg"):
            lp = Path("assets/legends") / f"{name_variant}.{ext}"
            if lp.exists():
                try: 
                    print(f"[CARD] Using local legend art: {lp}")
                    return Image.open(lp).convert("RGBA")
                except: pass

    # 2. Wiki fallback
    url = _get_wiki_art_url(legend_name)
    if url:
        data = await _fetch(url)
        if data:
            try: return Image.open(io.BytesIO(data)).convert("RGBA")
            except: pass
    return None


async def get_discord_pfp(pfp_url, size=100):
    data = await _fetch(pfp_url)
    if not data: return None
    try:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        img = img.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size-1, size-1], fill=255)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(img, mask=mask)
        return out
    except: return None


def _zone_center(zone_key):
    x0, y0, x1, y1 = ZONES[zone_key]
    return (x0+x1)//2, (y0+y1)//2


def _zone_size(zone_key):
    x0, y0, x1, y1 = ZONES[zone_key]
    return x1-x0, y1-y0


def _paste_legend(card, leg_img, zone_key, zones=None):
    if zones is None: zones = ZONES_S1
    x0, y0, x1, y1 = zones[zone_key]
    zw, zh = x1-x0, y1-y0
    sw, sh = leg_img.size
    scale = max(zw/sw, zh/sh)
    nw, nh = int(sw*scale), int(sh*scale)
    leg_img = leg_img.resize((nw, nh), Image.LANCZOS)
    cx = (nw-zw)//2
    cy = int(max(0, (nh-zh)*0.15))
    leg_img = leg_img.crop((cx, cy, cx+zw, cy+zh))
    mask = Image.new("L", (zw, zh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0,0,zw-1,zh-1], radius=8, fill=255)
    card.paste(leg_img, (x0, y0), mask)


def _draw_text_in_zone(draw, text, zone_key, font_size, color=(20,20,25), zones=None, y_offset=0):
    if zones is None: zones = ZONES_S1
    x0, y0, x1, y1 = zones[zone_key]
    cx = (x0+x1)//2
    cy = (y0+y1)//2 + y_offset
    zw = x1-x0-8

    font = _font(font_size)
    # Auto-shrink if too wide
    try:
        bbox = draw.textbbox((0,0), text, font=font)
        tw = bbox[2]-bbox[0]
        if tw > zw:
            font_size = int(font_size * zw / tw)
            font = _font(font_size)
    except: pass

    draw.text((cx, cy), text, font=font, fill=color, anchor="mm")


def _paste_pfp_in_zone(card, pfp, zone_key, zones=None):
    if pfp is None: return
    if zones is None: zones = ZONES_S1
    x0, y0, x1, y1 = zones[zone_key]
    zw, zh = x1-x0, y1-y0
    size = min(zw, zh)
    pfp_r = pfp.resize((size, size), Image.LANCZOS)
    cx = x0+(zw-size)//2
    cy = y0+(zh-size)//2
    card.paste(pfp_r, (cx, cy), pfp_r)


async def generate_card(username, avg_dmg, kd, assists, total_kills,
                        survival_time, ovr, legend_name, pfp_url, rarity=None, guild_id=None, role_override=None):
    if rarity is None:
        rarity = roll_rarity()

    rarity_name = rarity["name"]

    # Randomly pick a card style
    style = random.choice([1, 2, 3])
    if style == 1:
        templates = RARITY_TEMPLATES_S1
        zones = ZONES_S1
    elif style == 2:
        templates = RARITY_TEMPLATES_S2
        zones = ZONES_S2
    else:
        templates = RARITY_TEMPLATES_S3
        zones = ZONES_S3
    print(f"[CARD] Style {style} | {rarity_name} | OVR:{ovr} | {legend_name} | {username}")

    import asyncio
    leg_task = asyncio.create_task(get_legend_image(legend_name))
    pfp_task = asyncio.create_task(get_discord_pfp(pfp_url, 110)) if pfp_url else None
    leg_img  = await leg_task
    pfp_img  = await pfp_task if pfp_task else None

    role = role_override if role_override else LEGEND_TO_ROLE.get(legend_name.lower(), "FRAGGER")

    # Load template
    try:
        card = _load_template(rarity_name, templates)
    except FileNotFoundError as e:
        logger.error("Template missing: %s", e)
        card = Image.new("RGBA", (918, 1152), (230, 225, 210))

    draw = ImageDraw.Draw(card)

    # For Style 3 (dark card) use white boxes for text zones
    # For Styles 1 & 2 (light card) sample the background color
    if style == 3:
        bg_color = (255, 255, 255)  # white boxes on dark card
    else:
        bg_color = card.getpixel((150, 750))[:3]

    def blank(zone_key, color=None):
        x0, y0, x1, y1 = zones[zone_key]
        draw.rectangle([x0, y0, x1, y1], fill=color or bg_color)

    # Blank all placeholder zones
    blank("ovr")
    blank("role")
    blank("name")
    blank("stat_avgdmg", (255,255,255))
    blank("stat_kd",     (255,255,255))
    blank("stat_ast",    (255,255,255))
    blank("stat_kills",  (255,255,255))
    blank("stat_srt",    (255,255,255))

    # 1. Legend art
    if leg_img:
        _paste_legend(card, leg_img.convert("RGBA"), "art_box", zones)
        draw = ImageDraw.Draw(card)

    # 2. OVR number — large
    _draw_text_in_zone(draw, str(ovr), "ovr", font_size=88, color=(15,15,20), zones=zones)

    # 3. Role
    _draw_text_in_zone(draw, role, "role", font_size=30, color=(30,30,35), zones=zones)

    # 4. PFP
    _paste_pfp_in_zone(card, pfp_img, "pfp", zones)

    # 5. Username — lower text for Style 3
    name_offset = 5 if style == 3 else 0
    _draw_text_in_zone(draw, username.upper(), "name", font_size=70, color=(15,15,20), zones=zones, y_offset=name_offset)

    # 6. Stats
    stats = [
        ("stat_avgdmg", f"{int(avg_dmg):,}"),
        ("stat_kd",     f"{kd:.2f}"),
        ("stat_ast",    f"{assists:.1f}"),
        ("stat_kills",  f"{total_kills:,}"),
        ("stat_srt",    f"{survival_time:.1f}m"),
    ]
    for zone_key, value in stats:
        _draw_text_in_zone(draw, value, zone_key, font_size=38, color=(15,15,20), zones=zones)

    # ── Server logo overlay ──
    if guild_id and guild_id in SERVER_LOGOS:
        base_path = SERVER_LOGOS[guild_id]
        # Style 3 (dark card) uses white logo, styles 1 & 2 use black logo
        if style == 3:
            logo_path = base_path.replace("VESA_Black", "VESA_White")
        else:
            logo_path = base_path.replace("VESA_White", "VESA_Black")
        if os.path.exists(logo_path):
            try:
                x0, y0, x1, y1 = LOGO_ZONES[style]
                zw, zh = x1-x0, y1-y0
                # Blank the logo zone with style-appropriate background
                logo_bg = (0, 0, 0) if style == 3 else (255, 255, 255)
                draw.rectangle([x0, y0, x1, y1], fill=logo_bg)
                logo = Image.open(logo_path).convert("RGBA")
                logo = logo.resize((zw, zh), Image.LANCZOS)
                card.paste(logo, (x0, y0), logo)
                print(f"[CARD] Server logo applied for guild {guild_id}")
            except Exception as e:
                print(f"[CARD] Logo paste failed: {e}")

    buf = io.BytesIO()
    card.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()
# Wed Apr 29 02:43:25 UTC 2026
