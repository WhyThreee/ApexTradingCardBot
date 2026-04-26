# Apex Legends PlayerCard Bot

A Discord bot that generates collectible trading cards from Overstat.gg scrim stats.

---

## Features

- `/playercard <url> [legend]` — generates a full trading card PNG in the channel
- Weighted rarity roll on every generation (Common → HOLO)
- OVR rating calculated from weighted scrim stats
- Role archetype system (ANCHOR / FRAGGER / REFRAG / SUPPORT)
- Discord PFP automatically embedded as a circle on the card
- Legend art fetched and cached from the Apex Legends wiki
- Carbon fiber / brushed metal card aesthetic

---

## Project Structure

```
apex_playercard/
├── bot.py              ← Discord bot, slash command handler
├── scraper.py          ← Overstat.gg scraper
├── card_generator.py   ← PIL card image builder + rarity effects
├── ovr_calculator.py   ← OVR rating logic
├── constants.py        ← Roles, rarities, OVR weights, legend art URLs
├── requirements.txt
├── .env.example
├── assets/
│   ├── fonts/          ← Drop BebasNeue-Regular.ttf here
│   └── legends/        ← Optional: pre-place legend PNGs here
└── cache/
    └── legends/        ← Auto-populated legend art cache
```

---

## Setup

### 1. Clone / copy the project
```bash
git clone <your-repo>
cd apex_playercard
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Bebas Neue font (recommended)
Download **BebasNeue-Regular.ttf** from Google Fonts:
https://fonts.google.com/specimen/Bebas+Neue

Place it at: `assets/fonts/BebasNeue-Regular.ttf`

The bot falls back to a system font if this is missing, but Bebas Neue looks far better.

### 5. Create your Discord bot
1. Go to https://discord.com/developers/applications
2. Click **New Application**
3. Go to **Bot** → **Add Bot**
4. Under **Privileged Gateway Intents**, enable **Server Members Intent**
5. Copy the **Token**

### 6. Configure environment
```bash
cp .env.example .env
```
Edit `.env`:
```
DISCORD_TOKEN=your_token_here
```

### 7. Invite the bot to your server
In the Developer Portal:
- **OAuth2 → URL Generator**
- Scopes: `bot`, `applications.commands`
- Permissions: `Send Messages`, `Embed Links`, `Attach Files`, `Use Slash Commands`
- Copy the generated URL and open it in your browser

### 8. Run
```bash
python bot.py
```

On first run, slash commands are synced globally (can take up to 1 hour to propagate).
For faster testing, sync to a specific guild — see the note below.

---

## Usage

```
/playercard overstat_url:https://overstat.gg/player/2584.ColoHockey_/overview
/playercard overstat_url:https://overstat.gg/player/2584.ColoHockey_/overview legend:Wraith
```

**Parameters:**
| Parameter | Required | Description |
|---|---|---|
| `overstat_url` | ✅ | Full Overstat.gg profile URL |
| `legend` | ❌ | Override legend (defaults to most-played) |

---

## Rarity System

| Rarity | Chance | Visual |
|---|---|---|
| Common | 50.0% | Grey metallic frame |
| Rare | 25.0% | Blue frame |
| Epic | 15.0% | Purple frame |
| Legendary | 8.5% | Gold frame + glow |
| Mythic | 1.0% | Red frame + glow + pulse border |
| HOLO | 0.5% | Prismatic rainbow foil overlay |

---

## OVR Calculation

| Stat | Weight |
|---|---|
| AVG DMG | 35% |
| Assists | 25% |
| Top 5 Finishes | 20% |
| K/D Ratio | 12% |
| Survival Time | 8% |

Each stat is normalized against a performance ceiling, then scaled to 1–99.

---

## Role / Archetype System

| Role | Legends |
|---|---|
| ANCHOR | Caustic, Wattson, Rampart, Catalyst, Gibraltar, Newcastle, Vantage |
| FRAGGER | Bangalore, Revenant, Fuse, Mad Maggie, Ballistic, Wraith, Octane, Horizon, Ash |
| REFRAG | Pathfinder, Alter, Valkyrie, Seer, Crypto |
| SUPPORT | Lifeline, Mirage, Loba, Conduit |

---

## Deployment Options

### Local (development)
```bash
python bot.py
```

### Railway (recommended for 24/7 hosting)
1. Push code to a GitHub repo
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Add `DISCORD_TOKEN` as an environment variable
4. Set start command: `python bot.py`

### Render
1. Create a new **Background Worker** service
2. Connect your GitHub repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python bot.py`
5. Add `DISCORD_TOKEN` environment variable

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "bot.py"]
```

---

## Notes

- Legend art is cached locally after first fetch — subsequent cards generate faster.
- The scraper uses CSS/text heuristics since Overstat.gg doesn't have a public API.
  If the site updates its layout, `scraper.py` may need adjustments.
- Overstat profiles must be **public** to scrape.
- The bot requires the **Server Members Intent** to fetch Discord PFPs.
