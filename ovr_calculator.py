# ============================================================
#  ovr_calculator.py  —  Apex PlayerCard Bot
# ============================================================
"""
Converts raw scraped stats into a 1–99 OVR rating.

Weights (sum to 1.0):
    AVG DMG       35%
    Assists       25%
    Top 5         20%
    K/D           12%
    Survival Time  8%
"""

from constants import OVR_WEIGHTS, OVR_CEILINGS


def _score_stat(value: float, ceiling: float) -> float:
    """Return a 0–1 score for a single stat, clamped at the ceiling."""
    if ceiling <= 0:
        return 0.0
    return min(value / ceiling, 1.0)


def calculate_ovr(
    avg_dmg: float,
    assists: float,
    total_kills: int,
    kd: float,
    survival_time: float,
) -> int:
    """
    Returns an integer OVR in the range [1, 99].

    Parameters
    ----------
    avg_dmg       : Average damage per game.
    assists       : Average assists per game.
    total_kills   : Total kills across all tracked games.
    kd            : Kill / Death ratio.
    survival_time : Average survival time in minutes.
    """
    raw_scores = {
        "avg_dmg":       _score_stat(avg_dmg,       OVR_CEILINGS["avg_dmg"]),
        "assists":       _score_stat(assists,        OVR_CEILINGS["assists"]),
        "total_kills":   _score_stat(total_kills,   OVR_CEILINGS["total_kills"]),
        "kd":            _score_stat(kd,             OVR_CEILINGS["kd"]),
        "survival_time": _score_stat(survival_time,  OVR_CEILINGS["survival_time"]),
    }

    weighted = sum(raw_scores[stat] * OVR_WEIGHTS[stat] for stat in OVR_WEIGHTS)

    # Scale 0–1 to 1–99
    ovr = round(weighted * 98) + 1
    return max(1, min(99, ovr))
