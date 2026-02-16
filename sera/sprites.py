"""
Pixel art sprite library for SERA: ENDLESS ENGAGEMENT.

Old-school 64/128-bit style ASCII/Unicode art.
Uses block characters: ░▒▓█▀▄▐▌ and box-drawing for the retro feel.
"""

# ─────────────────────────────────────────────────────────
# Title / Logo
# ─────────────────────────────────────────────────────────

SERA_LOGO = r"""
  ░██████╗███████╗██████╗░░█████╗░
  ██╔════╝██╔════╝██╔══██╗██╔══██╗
  ╚█████╗░█████╗░░██████╔╝███████║
  ░╚═══██╗██╔══╝░░██╔══██╗██╔══██║
  ██████╔╝███████╗██║░░██║██║░░██║
  ╚═════╝░╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝
"""

SUBTITLE_ART = r"""
  ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄
  █  E N D L E S S  ENGAGEMENT  █
  ▀▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▀
"""

SERA_PORTRAIT = r"""
       ▄▄████▄▄
      ██▀░░░░▀██
     █▀ ▄▀▀▄ ▀█
     █  █◆ █  █
     █▄ ▀▄▄▀ ▄█
      ██▄░░▄██
     ▄█▀██████▀█▄
    ██░░░████░░░██
   ██░░░░░██░░░░░██
   █▌░░░░░██░░░░░▐█
   ██░░░░████░░░░██
    ▀█▄░░░░░░░░▄█▀
      ▀▀██████▀▀
"""

SERA_IDLE = r"""
     ▄▄██▄▄
    █▀░░░░▀█
    █ ◆  ◆ █
    ▀█▄──▄█▀
     ▄████▄
    ██░░░░██
    █▌░██░▐█
     █░░░░█
     ▐█▀▀█▌
"""

# ─────────────────────────────────────────────────────────
# Enemy Sprites (by archetype)
# ─────────────────────────────────────────────────────────

ENEMY_SPRITES = {
    "trash": r"""
     ▄▄▄
    █ x x █
    █  ▽  █
     ▀█▄█▀
      █ █
""",
    "elite": r"""
      ▄█▄
     ██░██
    █ ◈  ◈ █
    █▌ ▼▼ ▐█
     ██▄▄██
    ▄██████▄
    █▌░██░▐█
     ▀▀  ▀▀
""",
    "boss": r"""
    ░▄▄████▄▄░
    █▀▀░░░░▀▀█
   ██ ▓▓  ▓▓ ██
   █▌  ▀██▀  ▐█
    ██▄░▀▀░▄██
   ▄██████████▄
  ██▓░░██████░░▓██
  █▌░░░░░██░░░░░▐█
   ██░░░████░░░██
    ▀▀████████▀▀
""",
}

SKULL = r"""
     ▄▄███▄▄
    █▀░░░░░▀█
   █ ▓▓  ▓▓ █
   █  ▀██▀  █
    ▀▄░▀▀░▄▀
      ▀████▀
"""

TREASURE = r"""
    ▄████████▄
   ██▒▒▒▒▒▒▒▒██
   █▌▓▓▓▓▓▓▓▓▐█
   ██▒▒▒▒▒▒▒▒██
    ▀████████▀
"""

# ─────────────────────────────────────────────────────────
# Weapon Sprites
# ─────────────────────────────────────────────────────────

WEAPON_SPRITES = {
    "sword": r"""
       ▄
      ██
     ██
    ██
   █▀
  ▐▌
   ▀
""",
    "shiv": r"""
    ▄
   ██
   █▀
   ▐▌
    ▀
""",
    "maul": r"""
  ▄████▄
  █░░░░█
  ▀██▀▀
    ██
    ██
    ██
""",
    "axe": r"""
  ▄█▀▀▀
  █░░░
  ▀█▄▄▄█
    ██
    ██
""",
    "staff": r"""
   ◈
   ██
   ▐▌
   ▐▌
   ▐▌
   ▐▌
   ▀▀
""",
    "default": r"""
    ╋
   ╋
  ╋
""",
}

# ─────────────────────────────────────────────────────────
# Scene / Environment Art
# ─────────────────────────────────────────────────────────

DUNGEON_ENTRANCE = r"""
  ░░░░░▄████████▄░░░░░
  ░░░░██▒▒▒▒▒▒▒▒██░░░░
  ░░░██▒▒▒▒▒▒▒▒▒▒██░░░
  ░░██▒▒▒▒▒▒▒▒▒▒▒▒██░░
  ░██▒▒░░░░░░░░░░▒▒██░
  ██▒▒░░░░░░░░░░░░▒▒██
  ██▒▒░░░░░░░░░░░░▒▒██
  ██▒▒░░░░░░░░░░░░▒▒██
  ████████████████████
"""

GAME_OVER_ART = r"""
  ░░▄▄▄░░░▄▄▄░░░▄▄▄░░
  ▄█▓▓▓█▄█▓▓▓█▄█▓▓▓█▄
  █▓░░░▓██▓░░░▓██▓░░░▓█
  █▓░▀░▓██▓░▀░▓██▓░▀░▓█
  ▀█▓░▓█▀▀█▓░▓█▀▀█▓░▓█▀
   ▀███▀  ▀███▀  ▀███▀
"""

VICTORY_ART = r"""
        ░▄▄▄▄▄░
       ░█░░░░░█░
      ░██░▓▓▓░██░
     ░███░▓█▓░███░
    ░████░▓▓▓░████░
     ▀███████████▀
       ▀▀█████▀▀
          ███
         █████
        ▀▀▀▀▀▀▀
"""

CROWN = r"""
     ▄ ▄▄▄ ▄
    ▀█▀███▀█▀
     ▀█████▀
"""

# ─────────────────────────────────────────────────────────
# Combat Effects
# ─────────────────────────────────────────────────────────

HIT_EFFECT = r"""
    ╲ │ ╱
   ── ◆ ──
    ╱ │ ╲
"""

CRITICAL_HIT = r"""
   ╲  ║  ╱
  ══ ◆◆◆ ══
   ╱  ║  ╲
"""

MISS_EFFECT = r"""
   ~ ~ ~
  ~ MISS ~
   ~ ~ ~
"""

DODGE_EFFECT = r"""
  ░░     ░░
   ░░  ░░
    ░░░░
     ▸▸
"""

INTERRUPT_EFFECT = r"""
   ██╗
   ██║
   ╚═╝
   ██╗
   ╚═╝
"""

DOT_TICK = r"""
  ~ ▓ ~
   ▓▓▓
  ~ ▓ ~
"""

# ─────────────────────────────────────────────────────────
# Decorative elements
# ─────────────────────────────────────────────────────────

UPGRADE_ANVIL = r"""
     ▄████████▄
    ██▓▓▓▓▓▓▓▓██
    █▌▒▒▒▒▒▒▒▒▐█
     ██▓▓▓▓▓▓██
      ▀██████▀
       ██████
    ████████████
"""

SHARD = r"""
    ◇
   ◇◇◇
    ◇
"""

UPGRADE_LEVELS = {
    0: "░░░",
    1: "█░░",
    2: "██░",
    3: "███",
}


def get_upgrade_display(level: int, max_level: int = 3) -> str:
    """Get visual upgrade level indicator."""
    return UPGRADE_LEVELS.get(level, "░" * max_level)


DIVIDER_SWORD = "  ════════╤═══════╤════════"
DIVIDER_PIXEL = "  ░▒▓█▓▒░ ░▒▓█▓▒░ ░▒▓█▓▒░"
DIVIDER_DOTS = "  ·····················"
DIVIDER_DIAMOND = "  ◆─────────◆─────────◆"

FLOOR_BANNER_L = "╔══════════════════════════════════════════════════════════╗"
FLOOR_BANNER_R = "╚══════════════════════════════════════════════════════════╝"

# Patience mood indicators (pixel art faces)
MOOD_HAPPY = "[ ◕‿◕ ]"
MOOD_NEUTRAL = "[ ─_─ ]"
MOOD_ANNOYED = "[ ◔_◔ ]"
MOOD_ANGRY = "[ ▀_▀ ]"
MOOD_FURIOUS = "[ ×_× ]"


def get_mood(patience_pct: float) -> str:
    """Get Sera's mood face based on patience percentage."""
    if patience_pct > 0.8:
        return MOOD_HAPPY
    if patience_pct > 0.6:
        return MOOD_NEUTRAL
    if patience_pct > 0.4:
        return MOOD_ANNOYED
    if patience_pct > 0.2:
        return MOOD_ANGRY
    return MOOD_FURIOUS


def get_enemy_sprite(archetype: str) -> str:
    """Get the sprite for an enemy archetype."""
    return ENEMY_SPRITES.get(archetype, ENEMY_SPRITES["trash"])


def get_weapon_sprite(weapon_name: str) -> str:
    """Match weapon name to a sprite."""
    name_lower = weapon_name.lower()
    for key in WEAPON_SPRITES:
        if key in name_lower:
            return WEAPON_SPRITES[key]
    return WEAPON_SPRITES["default"]
