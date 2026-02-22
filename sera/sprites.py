"""
Pixel art sprite library for SERA: ENDLESS ENGAGEMENT.

Old-school 64/128-bit style ASCII/Unicode art.
Uses block characters: ░▒▓█▀▄▐▌ and box-drawing for the retro feel.
"""

import textwrap

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


ENEMY_NAME_SPRITES = {
    "flickering imp": r"""
      /\_/\
     ( o.o )
      > ^ <
     /|_|\
      / \
""",
    "wailing phantom": r"""
      .-''''-.
    .'  .-.  '.
   /   (   )   \
   |    `-'    |
   |  .-===-.  |
   | /  .-.  \ |
    \|  | |  |/
     '._|_|_.'
""",
    "moonbound werewolf": r"""
      /\___/\
     (  o o  )
     /   ^   \
    /|  ---  |\
   /_|_/   \_|_\
""",
    "clanking dreadknight": r"""
      .-===-.
     /  _ _  \
    |  |o o|  |
    |  | ^ |  |
    |  |_-_|  |
     \  ___  /
      ||||| |
      ||||| |
""",
    "ashen salamander": r"""
      __/\__
    _/  ..  \
   /  /__/\  \
   \__\  /__/
      /_/\_\
""",
    "lich narrator": r"""
      .-===-.
     / .===. \
     \/ 6 6 \/
     ( \___/ )
 ___ooo__V__ooo___
""",
    "rimebound golem": r"""
      ▄█▀▀█▄
     █░░░░░█
    █░█▀▀█░█
    █░█▄▄█░█
    ▀█░░░░█▀
      ▀██▀
""",
    "static oracle": r"""
      .-~~~~-.
     /  ⚡⚡  \
    |  .--.  |
    | (____) |
     \  ||  /
      '--'--
""",
    "stone golem": r"""
      ██████
     █ ▄▄▄▄ █
     █ █  █ █
     █ ████ █
      █ ▄▄ █
      ██████
""",
    "howling banshee": r"""
      .-oo-.
     / x  x\
    |   --  |
    |  \__/ |
    |  /  \ |
     \_/\/\_/
""",
    "plague rat swarm": r"""
     (\__/)(\__/)
    (='.'=)(='.'=)
    (")_(")(")_(")
""",
    "vain paladin": r"""
      .-^^-.
     /  __  \
    |  |++|  |
    |  |__|  |
    |   /\   |
     \  \/  /
      '----'
""",
    "withered vampyr": r"""
      /\  /\
     ( o  o )
     |  --  |
     | \__/ |
     |  /\  |
      \_||_/
""",
    "screaming specter": r"""
      .----.
     / 0  0 \
    |   __   |
    |  /  \  |
    |  \__/  |
     \______/
""",
    "iron troll": r"""
      ▄████▄
     █░█▄▄█░█
     █░░██░░█
     █░████░█
      █░██░█
      ██████
""",
    "barrow witch": r"""
       /\
      /__\
     ( .. )
     /|==|\
    /_|__|_\
      /  \
""",
    "void stalker": r"""
      .::::.
     : x  x:
     :  -- :
      \ -- /
     .-====-.
    /  ||||  \
""",
    "rusted automaton": r"""
      .----.
     | [] []|
     |  __  |
     | |__| |
     |______|
      / || \
""",
    "gilded revenant": r"""
      .-**-.
     / 00  \
    |  __   |
    | |==|  |
    | |__|  |
     \____/
""",
    "mirrorborn doppelganger": r"""
      /\__/\
     ( o  o )
     |  ><  |
     | /--\ |
     | \__/ |
      \____/
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
    "rusty shiv": r"""
    ▄
   ██
   █▀
   ▐▌
    ▀
""",
    "iron claymore": r"""
      ▄
     ███
    ███
   ███
   ▐█▌
    ██
    ▀▀
""",
    "bone whip": r"""
   _/\
  /  /~~
 /  /~~~
 \_/____
    ||
""",
    "forbidden tome": r"""
   ██████
   █▌◈◈▐█
   █▌██▐█
   ██████
""",
    "silver rapier": r"""
      /|
     / |
    /  |
   /   |
  (====|
      / 
""",
    "acid vial": r"""
    ▄▄▄
   █░░█
   █▓▓█
   █▄▄█
    ▀▀
""",
    "ember staff": r"""
    ✶
    █
    █
    █
    █
    ▀
""",
    "war maul": r"""
  ▄████▄
  █░░░░█
  ▀██▀▀
    ██
    ██
    ██
""",
    "spirit lantern": r"""
   .--.
  / oo \
  | || |
  | || |
  '----'
""",
    "sonic bell": r"""
    .--.
   / __ \
  / /  \ \
  \ \__/ /
   '----'
""",
    "frozen scepter": r"""
    ❄
    █
    █
    █
    ▀
""",
    "chain hook": r"""
   o-o-o-
        \
         )
        /
""",
    "runic greataxe": r"""
  ████▀
  █◈◈█ 
  ▀███▄
    ██
    ██
""",
    "venom fang dagger": r"""
    /\
   /██
   \██
    \/
    ||
""",
    "thunderclap gauntlet": r"""
   .-.-.
  ( ⚡⚡ )
   |██|
   |██|
""",
    "spectral scythe": r"""
   .----)
  /  __/
 /  /
 |  |
 |  |
""",
    "molten flail": r"""
   ███
  █▓▓█
   ███
    o-o-o
      |
""",
    "blessed mace": r"""
   ✚
  ███
   █
   █
   █
""",
    "shadow needle": r"""
    |
    |
    |
    |
    v
""",
    "alchemist's crossbow": r"""
  }===>
  ||-||
  || ||
   \_/
""",
    "frostbite dagger": r"""
    /\
   /❄█
   \██
    \/
""",
    "inferno pike": r"""
    ^
   /█\
    █
    █
    █
""",
    "stormglass wand": r"""
   ◇
   │
   │
   │
   └
""",
    "glacier chakram": r"""
   .----.
  / ❄  \
  \  ❄ /
   '----'
""",
    "godsthorn needle": r"""
    †
    |
    |
    |
    v
""",
    "obsidian cleaver": r"""
   ████
   ████▌
    ███▌
     ██
     ██
""",
    "runebrand whip": r"""
   /◈\~~
  /◈/~~~
  \_/____
    ||
""",
    "ashen crossbow": r"""
  }===>>
  ||##||
  ||##||
   \__/
""",
    "void crystal": r"""
    /\
   /  \
   \  /
    \/
    ||
""",
    "bile flask": r"""
   .--.
  / oo \
  |▓▓▓|
  |▄▄▄|
""",
    "silver moonshard": r"""
    /\
   /  \
  / ◐  \
  \    /
   \  /
""",
    "siren's harp": r"""
   ╭──╮
   │))│
   │))│
   │))│
   ╰──╯
""",
    "frozen greatclub": r"""
  █████
  █❄❄█
  █████
    ██
    ██
""",
    "judgment gauntlet": r"""
   .---.
  /  †  \
  | [ ] |
  | [ ] |
   '---'
""",
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


def get_enemy_sprite(archetype: str, enemy_name: str = "") -> str:
    """Get sprite by enemy name first, then archetype fallback."""
    key = enemy_name.strip().lower()
    if key in ENEMY_NAME_SPRITES:
        return textwrap.dedent(ENEMY_NAME_SPRITES[key])
    return textwrap.dedent(ENEMY_SPRITES.get(archetype, ENEMY_SPRITES["trash"]))


def get_weapon_sprite(weapon_name: str) -> str:
    """Match weapon name to a sprite."""
    name_lower = weapon_name.lower()
    for key in WEAPON_SPRITES:
        if key in name_lower:
            return WEAPON_SPRITES[key]
    return WEAPON_SPRITES["default"]
