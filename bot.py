# ============================================================
#  bot.py  —  Apex PlayerCard Discord Bot
# ============================================================
"""
Run with:
    python bot.py

Requires:
    - DISCORD_TOKEN in .env
    - pip install -r requirements.txt
"""

import os
import re
import logging
import traceback
import asyncio
from typing import Optional
from collections import defaultdict
import time

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from scraper import scrape_player
from ovr_calculator import calculate_ovr
from card_generator import generate_card, roll_rarity
from constants import LEGEND_TO_ROLE, LEGEND_ART_URLS

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("apex_bot")

# ------------------------------------------------------------------
# Bot setup
# ------------------------------------------------------------------

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ── Rate limiting & queue ─────────────────────────────────────
# Max 1 request per user per 30 seconds
RATE_LIMIT_SECONDS = 0
user_last_request: dict[int, float] = {}

# Global semaphore — max 3 cards generating at once
# Prevents server overload with 1k users
CARD_SEMAPHORE = asyncio.Semaphore(3)


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------

def _resolve_legend_name(legend_input: Optional[str], scraped_legend: str) -> str:
    """
    Return a valid legend name.
    If user provided one, validate it. Otherwise use the scraped default.
    Passing 'random' picks a random legend from the full roster.
    """
    if not legend_input:
        return scraped_legend

    normalized = legend_input.strip().lower()[:50]  # cap length

    # Random legend roll
    if normalized == "random":
        import random
        chosen = random.choice(list(LEGEND_ART_URLS.keys()))
        logger.info("Random legend rolled: %s", chosen)
        return chosen.title()

    if normalized in LEGEND_ART_URLS:
        return legend_input.strip().title()

    # Fuzzy match: check if it's a substring of a known legend
    for known in LEGEND_ART_URLS:
        if normalized in known or known in normalized:
            return known.title()

    logger.warning("Unknown legend '%s', using scraped default '%s'", legend_input, scraped_legend)
    return scraped_legend


def _format_survival(raw: float) -> str:
    """Round survival time to one decimal."""
    return f"{raw:.1f}m"


# ------------------------------------------------------------------
# /playercard command
# ------------------------------------------------------------------

@tree.command(
    name="playercard",
    description="Generate your Apex Legends scrim player card from Overstat.gg",
)
@app_commands.describe(
    overstat_url="Your Overstat.gg profile URL  (e.g. https://overstat.gg/player/123.YourName/overview)",
    legend="(Optional) Legend name, or 'random'. Defaults to your most-played.",
    role="(Optional) Your role: ANCHOR, FRAGGER, REFRAG, or SUPPORT. Overrides auto-detected role.",
)
async def playercard(
    interaction: discord.Interaction,
    overstat_url: str,
    legend: Optional[str] = None,
    role: Optional[str] = None,
):
    """
    Slash command: /playercard <overstat_url> [legend]

    Flow:
    1. Defer reply (card gen takes a moment)
    2. Scrape Overstat profile
    3. Calculate OVR
    4. Roll rarity
    5. Fetch Discord PFP from the command author
    6. Generate card PNG
    7. Post in channel
    """
    await interaction.response.defer(thinking=True)

    # ── Rate limit check ──────────────────────────────────────────
    user_id = interaction.user.id
    now = time.time()
    last = user_last_request.get(user_id, 0)
    if now - last < RATE_LIMIT_SECONDS:
        wait = int(RATE_LIMIT_SECONDS - (now - last))
        await interaction.followup.send(
            f"⏳ Please wait **{wait}s** before generating another card.",
            ephemeral=True
        )
        return
    user_last_request[user_id] = now

    # ── Queue check — max 3 concurrent generations ────────────────
    if CARD_SEMAPHORE.locked():
        await interaction.followup.send(
            "🔄 The bot is busy generating cards. Please try again in a few seconds!",
            ephemeral=True
        )
        return

    # ── Step 1: Validate URL ──────────────────────────────────────
    url_clean = overstat_url.strip()[:300]
    if not url_clean.lower().startswith("https://overstat.gg/player/"):
        await interaction.followup.send(
            "❌ Please provide a valid **Overstat.gg** profile URL.\n"
            "Example: `https://overstat.gg/player/2584.ColoHockey_/overview`",
            ephemeral=True,
        )
        return
    if any(c in url_clean for c in [";", "&", "|", "`", "$", "(", ")", "\n", "\r"]):
        await interaction.followup.send("❌ Invalid URL format.", ephemeral=True)
        return
    overstat_url = url_clean

    # ── Step 2: Scrape ───────────────────────────────────────────
    try:
        player_data = await scrape_player(overstat_url)
    except Exception as e:
        logger.error("Scrape failed: %s\n%s", e, traceback.format_exc())
        await interaction.followup.send(
            f"❌ Could not fetch data from Overstat.gg. "
            f"Make sure the URL is correct and the profile is public.\n`{e}`",
            ephemeral=True,
        )
        return

    # ----------------------------------------------------------------
    # Step 3: Resolve legend
    # ----------------------------------------------------------------
    # Strip any HTML/injection chars from legend input
    if legend:
        legend = re.sub(r"[<>{}\[\]\\]", "", legend).strip()[:50]
    resolved_legend = _resolve_legend_name(legend, player_data["most_played_legend"])

    # ── Validate and apply custom role ───────────────────────────
    VALID_ROLES = ["ANCHOR", "FRAGGER", "REFRAG", "SUPPORT", "IGL"]
    resolved_role = None
    if role:
        role_upper = role.strip().upper()[:20]  # limit length
        if role_upper in VALID_ROLES:
            resolved_role = role_upper
        else:
            await interaction.followup.send(
                f"❌ Invalid role `{role}`. Choose from: ANCHOR, FRAGGER, REFRAG, SUPPORT, IGL",
                ephemeral=True,
            )
            return

    # ----------------------------------------------------------------
    # Step 4: Calculate OVR
    # ----------------------------------------------------------------
    ovr = calculate_ovr(
        avg_dmg=player_data["avg_dmg"],
        assists=player_data["assists"],
        total_kills=player_data["total_kills"],
        kd=player_data["kd"],
        survival_time=player_data["survival_time"],
    )

    # ----------------------------------------------------------------
    # Step 5: Roll rarity
    # ----------------------------------------------------------------
    rarity = roll_rarity()
    logger.info(
        "Card for %s — legend=%s ovr=%d rarity=%s",
        player_data["username"], resolved_legend, ovr, rarity["name"],
    )

    # ----------------------------------------------------------------
    # Step 6: Fetch Discord PFP
    # ----------------------------------------------------------------
    pfp_url: Optional[str] = None
    try:
        member = interaction.user
        if member.avatar:
            pfp_url = str(member.avatar.replace(format="png", size=256))
        elif member.default_avatar:
            pfp_url = str(member.default_avatar.replace(format="png", size=256))
    except Exception as e:
        logger.warning("Could not resolve PFP: %s", e)

    # ----------------------------------------------------------------
    # Step 7: Generate card
    # ----------------------------------------------------------------
    async with CARD_SEMAPHORE:
        try:
            discord_name = interaction.user.display_name[:32].replace('@', '').replace('`', '')
            card_bytes = await generate_card(
                username=discord_name,
                avg_dmg=player_data["avg_dmg"],
                kd=player_data["kd"],
                assists=player_data["assists"],
                total_kills=player_data["total_kills"],
                survival_time=player_data["survival_time"],
                ovr=ovr,
                legend_name=resolved_legend,
                pfp_url=pfp_url,
                rarity=rarity,
                guild_id=interaction.guild_id,
                role_override=resolved_role,
            )
        except Exception as e:
            logger.error("Card generation failed: %s\n%s", e, traceback.format_exc())
            await interaction.followup.send(
                f"❌ Card generation failed. Please try again.\n`{e}`",
                ephemeral=True,
            )
            return

    # ----------------------------------------------------------------
    # Step 8: Post card publicly
    # ----------------------------------------------------------------
    file = discord.File(
        fp=__import__("io").BytesIO(card_bytes),
        filename=f"{player_data['username']}_playercard.png",
    )

    rarity_emoji = {
        "COMMON": "⬜",
        "RARE": "🟦",
        "EPIC": "🟪",
        "LEGENDARY": "🟨",
        "MYTHIC": "🟥",
        "HOLO": "🌈",
    }.get(rarity["name"], "⬜")

    safe_username = player_data['username'].replace('@','').replace('`','').replace('*','')[:32]
    embed = discord.Embed(
        title=f"{rarity_emoji} {safe_username.upper()} — {rarity['name']} CARD",
        description=(
            f"**Legend:** {resolved_legend}  |  "
            f"**OVR:** {ovr}  |  "
            f"**Rarity:** {rarity['name']}"
        ),
        color=discord.Color.from_rgb(*rarity["frame_color"]),
    )
    embed.set_image(url=f"attachment://{player_data['username']}_playercard.png")
    embed.set_footer(
        text=f"Requested by {discord_name}  •  Data from Overstat.gg",
        icon_url=pfp_url or "",
    )

    await interaction.followup.send(embed=embed, file=file)


# ------------------------------------------------------------------
# Bot events
# ------------------------------------------------------------------

@bot.event
async def on_ready():
    synced = await tree.sync()
    logger.info("✅ Bot ready — logged in as %s (ID: %s)", bot.user, bot.user.id)
    logger.info("Slash commands synced: %d commands", len(synced))


@bot.event
async def on_application_command_error(interaction: discord.Interaction, error):
    logger.error("Unhandled command error: %s", error)
    try:
        await interaction.followup.send(
            "❌ An unexpected error occurred. Please try again.", ephemeral=True
        )
    except Exception:
        pass


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN not found. "
            "Create a .env file with DISCORD_TOKEN=your_token_here"
        )
    bot.run(token)
# Force redeploy
