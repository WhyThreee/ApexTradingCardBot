# ============================================================
#  card_generator.py  —  Apex PlayerCard Bot  (v9 - Template)
# ============================================================
"""
Template-based card compositor.
Loads your designed card templates and composites dynamic
content (legend art, stats, username, OVR, PFP) at exact
pixel coordinates measured from your border maps.
"""

import io, os, math, random, logging, urllib.request, json
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image, ImageDraw, ImageFont

from constants import LEGEND_TO_ROLE, RARITIES, RARITY_WEIGHTS, LEGEND_ART_URLS
# Imagen removed - using wiki art fallback

logger = logging.getLogger(__name__)
FONT_DIR   = "assets/fonts"
TEMPLATE_DIR = "assets/templates"

# ── Rarity → template file mapping ───────────────────────────
RARITY_TEMPLATES = {
    "COMMON":    "Blue_Style 1.png",    # fallback to blue if no common
    "RARE":      "Blue_Style 1.png",
    "EPIC":      "Purple_Style 1.png",
    "LEGENDARY": "Gold_Style 1.png",
    "MYTHIC":    "Red_Style 1.png",
    "HOLO":      "Holo_Style 1.png",
}

# ── Zone coordinates (x0, y0, x1, y1) ────────────────────────
# Measured precisely from your border map image
ZONES = {
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


# ── Fonts ─────────────────────────────────────────────────────
def _font(size):
    for p in [
        os.path.join(FONT_DIR, "BebasNeue-Regular.ttf"),
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()


def roll_rarity():
    return random.choices(RARITIES, weights=RARITY_WEIGHTS, k=1)[0]


# ── Template loader ───────────────────────────────────────────
def _load_template(rarity_name: str) -> Image.Image:
    """Load the card template for the given rarity."""
    fname = RARITY_TEMPLATES.get(rarity_name, "Blue_Style_1.png")

    # Check template dir first
    tpath = Path(TEMPLATE_DIR) / fname
    if tpath.exists():
        return Image.open(tpath).convert("RGBA")

    # Fallback: check uploads dir (for development)
    upath = Path("/mnt/user-data/uploads") / fname
    if upath.exists():
        return Image.open(upath).convert("RGBA")

    raise FileNotFoundError(f"Template not found: {fname}")


# ── Image fetchers ────────────────────────────────────────────
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
    # 1. Local assets
    key = legend_name.lower().replace(" ", "_")
    for ext in ("png", "webp", "jpg"):
        lp = Path("assets/legends") / f"{key}.{ext}"
        if lp.exists():
            try: return Image.open(lp).convert("RGBA")
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


# ── Compositor helpers ────────────────────────────────────────
def _zone_size(zone_key):
    x0, y0, x1, y1 = ZONES[zone_key]
    return x1 - x0, y1 - y0


def _paste_zone(card, img, zone_key, radius=0):
    """Paste an image into a zone, scaled to fit."""
    x0, y0, x1, y1 = ZONES[zone_key]
    zw, zh = x1 - x0, y1 - y0

    # Scale to fill zone
    sw, sh = img.size
    scale = min(zw / sw, zh / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.LANCZOS)

    # Center in zone
    ox = x0 + (zw - nw) // 2
    oy = y0 + (zh - nh) // 2

    if radius > 0:
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, img.size[0]-1, img.size[1]-1], radius=radius, fill=255)
        card.paste(img, (ox, oy), mask)
    else:
        if img.mode == "RGBA":
            card.paste(img, (ox, oy), img)
        else:
            card.paste(img, (ox, oy))


def _paste_legend(card, leg_img, zone_key):
    """Paste legend art to fill the art box, cropped to fit."""
    x0, y0, x1, y1 = ZONES[zone_key]
    zw, zh = x1 - x0, y1 - y0

    sw, sh = leg_img.size
    # Scale to fill (may crop)
    scale = max(zw / sw, zh / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    leg_img = leg_img.resize((nw, nh), Image.LANCZOS)

    # Crop center, bias toward top (show face/torso)
    cx = (nw - zw) // 2
    cy = int(max(0, (nh - zh) * 0.15))
    leg_img = leg_img.crop((cx, cy, cx + zw, cy + zh))

    # Paste with rounded corners
    mask = Image.new("L", (zw, zh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, zw-1, zh-1], radius=8, fill=255)
    card.paste(leg_img, (x0, y0), mask)


def _draw_text_zone(draw, text, zone_key, font_size, color=(20, 20, 25), anchor="mm"):
    """Draw centered text in a zone."""
    x0, y0, x1, y1 = ZONES[zone_key]
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2

    # Auto-fit font size if text is wide
    font = _font(font_size)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        zw = x1 - x0 - 8
        if tw > zw:
            font_size = int(font_size * zw / tw)
            font = _font(font_size)
    except: pass

    draw.text((cx, cy), text, font=font, fill=color, anchor=anchor)


def _paste_pfp_zone(card, pfp, zone_key):
    """Paste circular PFP centered in zone."""
    if pfp is None: return
    x0, y0, x1, y1 = ZONES[zone_key]
    zw, zh = x1 - x0, y1 - y0
    size = min(zw, zh)
    pfp_r = pfp.resize((size, size), Image.LANCZOS)
    cx = x0 + (zw - size) // 2
    cy = y0 + (zh - size) // 2
    card.paste(pfp_r, (cx, cy), pfp_r)


# ── Main compositor ───────────────────────────────────────────
async def generate_card(
    username, avg_dmg, kd, assists, total_kills,
    survival_time, ovr, legend_name, pfp_url, rarity=None
):
    if rarity is None:
        rarity = roll_rarity()

    rarity_name = rarity["name"]

    # Fetch assets concurrently
    import asyncio
    leg_task = asyncio.create_task(get_legend_image(legend_name))
    pfp_task = asyncio.create_task(get_discord_pfp(pfp_url, 110)) if pfp_url else None
    leg_img  = await leg_task
    pfp_img  = await pfp_task if pfp_task else None

    role = LEGEND_TO_ROLE.get(legend_name.lower(), "FRAGGER")

    print(f"[CARD] {rarity_name} | OVR:{ovr} | {legend_name} | {username}")

    # Load template
    try:
        card = _load_template(rarity_name)
    except FileNotFoundError as e:
        logger.error("Template missing: %s", e)
        # Create blank fallback
        card = Image.new("RGBA", (918, 1152), (230, 225, 210))

    draw = ImageDraw.Draw(card)

    # ── 0. Blank out placeholder zones with background color ──
    # Sample background color from a safe area (bottom-left cream area)
    bg_color = card.getpixel((150, 750))[:3]  # cream background

    def blank_zone(zone_key, color=None):
        x0, y0, x1, y1 = ZONES[zone_key]
        c = color or bg_color
        draw.rectangle([x0, y0, x1, y1], fill=c)

    blank_zone("ovr")
    blank_zone("role")
    blank_zone("name")
    blank_zone("stat_avgdmg",  (255,255,255))
    blank_zone("stat_kd",      (255,255,255))
    blank_zone("stat_ast",     (255,255,255))
    blank_zone("stat_kills",   (255,255,255))
    blank_zone("stat_srt",     (255,255,255))

    # ── 1. Legend art → art box ──
    if leg_img:
        _paste_legend(card, leg_img.convert("RGBA"), "art_box")
        draw = ImageDraw.Draw(card)

    # ── 2. OVR number ──
    _draw_text_zone(draw, str(ovr), "ovr", font_size=90,
                    color=(15, 15, 20), anchor="mm")

    # ── 3. Role / Type ──
    _draw_text_zone(draw, role, "role", font_size=28,
                    color=(30, 30, 35), anchor="mm")

    # ── 4. Discord PFP ──
    _paste_pfp_zone(card, pfp_img, "pfp")

    # ── 5. Username ──
    _draw_text_zone(draw, username.upper(), "name", font_size=72,
                    color=(15, 15, 20), anchor="mm")

    # ── 6. Stats ──
    stats = [
        ("stat_avgdmg", f"{int(avg_dmg):,}"),
        ("stat_kd",     f"{kd:.2f}"),
        ("stat_ast",    f"{assists:.1f}"),
        ("stat_kills",  f"{total_kills:,}"),
        ("stat_srt",    f"{survival_time:.1f}m"),
    ]
    for zone_key, value in stats:
        _draw_text_zone(draw, value, zone_key, font_size=36,
                        color=(15, 15, 20), anchor="mm")

    # ── Export ──
    buf = io.BytesIO()
    card.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()
