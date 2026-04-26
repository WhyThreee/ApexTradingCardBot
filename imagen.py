# ============================================================
#  imagen.py  —  Apex PlayerCard Bot
# ============================================================
"""
Generates cinematic legend portrait images using Google's
Imagen 3 API via the Gemini platform.
"""

import os
import io
import base64
import logging
import asyncio
from typing import Optional

import httpx
from PIL import Image

logger = logging.getLogger(__name__)

IMAGEN_URL = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"


LEGEND_PROMPTS = {
    "bangalore":   "Bangalore female soldier Apex Legends character, dramatic cinematic portrait, dark military armor, smoke grenade, intense expression, rim lighting, photorealistic, trading card art style, upper body, plain dark background",
    "bloodhound":  "Bloodhound Apex Legends character, dramatic cinematic portrait, ornate plague doctor mask, raven, mystical glowing eyes, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "caustic":     "Caustic Apex Legends character, dramatic cinematic portrait, gas mask scientist, toxic green glow, menacing expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "crypto":      "Crypto Apex Legends character, dramatic cinematic portrait, hacker drone operator, tech suit, holographic displays, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "fuse":        "Fuse Apex Legends character, dramatic cinematic portrait, australian explosives expert, mechanical arm, grenades, grinning expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "gibraltar":   "Gibraltar Apex Legends character, dramatic cinematic portrait, large protective shield, polynesian warrior armor, confident smile, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "horizon":     "Horizon Apex Legends character, dramatic cinematic portrait, scottish scientist, gravity lift technology, space suit, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "lifeline":    "Lifeline Apex Legends character, dramatic cinematic portrait, combat medic, yellow armor, healing drone, determined expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "loba":        "Loba Apex Legends character, dramatic cinematic portrait, elegant thief, purple outfit, jump drive bracelet, confident smirk, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "mirage":      "Mirage Apex Legends character, dramatic cinematic portrait, holographic trickster, slick hair, charming smile, hologram decoys, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "newcastle":   "Newcastle Apex Legends character, dramatic cinematic portrait, heroic knight armor, shield, blue energy, protective stance, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "octane":      "Octane Apex Legends character, dramatic cinematic portrait, adrenaline junkie, metal legs, stim injector, wild grin, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "pathfinder":  "Pathfinder Apex Legends character, dramatic cinematic portrait, friendly MRVN robot, grappling hook, smiley face screen, thumbs up, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "rampart":     "Rampart Apex Legends character, dramatic cinematic portrait, minigun turret expert, mohawk hair, mechanical armor, fierce expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "revenant":    "Revenant Apex Legends character, dramatic cinematic portrait, simulacrum assassin, skull face, dark metallic body, menacing pose, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "seer":        "Seer Apex Legends character, dramatic cinematic portrait, micro-drones artist, elaborate costume, glowing blue eyes, butterflies, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "valkyrie":    "Valkyrie Apex Legends character, dramatic cinematic portrait, jetpack warrior, winged armor, japanese pilot aesthetic, fierce expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "vantage":     "Vantage Apex Legends character, dramatic cinematic portrait, sniper scout, bat companion, survival suit, intense focus, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "wattson":     "Wattson Apex Legends character, dramatic cinematic portrait, electrical engineer, tesla coil weapon, blue electricity, cheerful expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "wraith":      "Wraith Apex Legends character, dramatic cinematic portrait, interdimensional skirmisher, void powers, tactical outfit, intense focused expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "ash":         "Ash Apex Legends character, dramatic cinematic portrait, simulacrum assassin, split face half robot half human, phase runner sword, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "mad maggie":  "Mad Maggie Apex Legends character, dramatic cinematic portrait, warlord rebel, war paint face, drill launcher, ferocious expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "ballistic":   "Ballistic Apex Legends character, dramatic cinematic portrait, veteran gunslinger, tactical vest, grey hair, cool composed expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "conduit":     "Conduit Apex Legends character, dramatic cinematic portrait, shield battery engineer, energy armor, bright smile, electric powers, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "alter":       "Alter Apex Legends character, dramatic cinematic portrait, void manipulator, dark outfit, portal rift, mysterious expression, rim lighting, photorealistic, trading card art style, upper body, dark background",
    "catalyst":    "Catalyst Apex Legends character, dramatic cinematic portrait, dark ferrofluid mage, flowing black liquid armor, glowing purple eyes, rim lighting, photorealistic, trading card art style, upper body, dark background",
}

DEFAULT_PROMPT = "Apex Legends character, dramatic cinematic portrait, futuristic armor, intense expression, rim lighting, photorealistic, trading card art style, upper body, dark background"


async def generate_legend_portrait(legend_name: str) -> Optional[Image.Image]:
    """
    Generate a cinematic legend portrait using Imagen 3.
    Returns a PIL Image or None on failure.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set — skipping Imagen generation")
        return None

    key = legend_name.lower().strip()
    prompt = LEGEND_PROMPTS.get(key, DEFAULT_PROMPT.replace("Apex Legends character", f"{legend_name} from Apex Legends"))

    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "3:4",
            "safetyFilterLevel": "block_few",
            "personGeneration": "allow_adult",
        }
    }

    url = f"{IMAGEN_URL}?key={api_key}"

    try:
        logger.info("Generating Imagen portrait for %s...", legend_name)
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Extract base64 image
        predictions = data.get("predictions", [])
        if not predictions:
            logger.warning("Imagen returned no predictions for %s", legend_name)
            return None

        b64 = predictions[0].get("bytesBase64Encoded")
        if not b64:
            logger.warning("Imagen prediction missing image data")
            return None

        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        logger.info("Imagen portrait generated successfully for %s (%dx%d)", legend_name, img.width, img.height)
        return img

    except httpx.HTTPStatusError as e:
        logger.error("Imagen API error %s: %s", e.response.status_code, e.response.text[:300])
        return None
    except Exception as e:
        logger.error("Imagen generation failed: %s", e)
        return None
