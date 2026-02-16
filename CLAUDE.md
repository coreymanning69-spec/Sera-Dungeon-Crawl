# CLAUDE.md — Sera: Endless Engagement

## Project Overview

A text-based, turn-based roguelike dungeon crawler written in pure Python 3. The player controls Sera, a bored Goddess who must be kept entertained through aggressive, interesting gameplay across 5 dungeon floors. The unique lose condition is **Patience** (not HP) — if Sera gets bored, she leaves and the game ends.

**Genre:** Systems-heavy roguelike with transparent math and small-number design.

## Quick Reference

```bash
# Play the game
python3 play.py

# Run demo scenarios (3 scripted combat simulations)
python3 main.py

# Platform launchers
./play.sh      # Unix/Linux/Mac
play.bat        # Windows
```

**No external dependencies.** Standard library only (`json`, `pathlib`, `dataclasses`, `enum`, `random`, `copy`, `os`).

**No build step, no package manager, no virtual environment required.**

## Repository Structure

```
.
├── play.py              # Interactive game entry point (~2,087 lines)
├── main.py              # Demo script: 3 scripted combat scenarios
├── play.sh              # Unix launcher (auto-detects python3/python)
├── play.bat             # Windows launcher
├── sera/                # Core game engine package
│   ├── __init__.py      # Package marker
│   ├── weapon.py        # Weapon + Affix dataclasses, damage pipeline
│   ├── enemy.py         # Enemy class, abilities, annoyance types
│   ├── combat.py        # Combat resolver (turn loop, damage calc)
│   ├── interest.py      # Patience engine (Sera's "HP" system)
│   ├── tags.py          # DamageTag + EnemyVulnerability enums
│   ├── status.py        # StatusEffect + StatusInstance (debuffs/DoT)
│   ├── crafting.py      # Crafting materials, weapon modification
│   ├── encounters.py    # Encounter generator, loot drops, scaling
│   ├── loader.py        # JSON data loader → game objects
│   └── ui.py            # ASCII box-drawn UI renderer (width=60)
└── data/                # JSON configuration (data-driven design)
    ├── weapons.json     # 10 base weapons (1-3 base damage, various tags)
    ├── affixes.json     # 10 prefix/suffix definitions
    └── enemies.json     # 5 enemy archetypes (trash/elite/boss)
```

## Architecture

### Layer Separation

| Layer | Files | Role |
|-------|-------|------|
| **Logic** | `sera/weapon.py`, `enemy.py`, `combat.py`, `interest.py`, `tags.py`, `status.py`, `crafting.py` | Game rules, math, state |
| **Data** | `sera/loader.py`, `sera/encounters.py`, `data/*.json` | Content definitions, generation |
| **View** | `sera/ui.py` | ASCII box rendering, display formatting |
| **Controller** | `play.py` | Interactive game loop, input handling |
| **Demo** | `main.py` | Scripted scenarios for testing/showcase |

### Core Systems

**Damage Pipeline** (`weapon.py` + `combat.py`):
1. Start with `base_damage` (1-3)
2. Add flat bonuses from affixes (conditional)
3. Apply multipliers from affixes (conditional)
4. Add per-stack bonuses (e.g., +1 per debuff on target)
5. Clamp result to `[0, 30]`

All math is transparent — every step is logged and shown to the player.

**Patience Engine** (`interest.py`):
- Starts at 100, drains by 1 per turn + enemy annoyance costs
- Restored by kills (+5), overkill (+excess damage), multi-kills (+10)
- Game over at 0

**Permission System** (`tags.py`):
- Weapons have `DamageTag` enums (PHYSICAL, DIVINE, SILVER, FIRE, etc.)
- Enemies have `EnemyVulnerability` requirements (e.g., REQUIRES_DIVINE)
- Wrong weapon = 0 damage + annoyance penalty

**Encounter Scaling** (`encounters.py`):
- Floor 1: 1 trash (tutorial)
- Floor 2: 2 trash
- Floor 3-4: 1 elite or 2-3 trash
- Floor 5: Boss + 1 trash escort
- Enemy HP scales +10% per floor past 1; armor scales for armored enemies

### Data-Driven Design

Weapons, affixes, and enemies are defined in `data/*.json` and loaded by `sera/loader.py`. Affix conditions are string keys (e.g., `"enemy_full_hp"`, `"first_hit"`, `"always"`) resolved dynamically by the combat resolver.

## Coding Conventions

### Style

- **Python 3** with modern features: `from __future__ import annotations`, type hints, `dataclasses`, `Enum`
- Union types use `X | None` syntax (Python 3.10+)
- Every module has a docstring header explaining its purpose in Sera's voice
- Section separators use `# ---------------------------------------------------------------------------` comment blocks
- Classes use `@dataclass` wherever possible
- Enums use `auto()` values throughout

### Naming

- Classes: `PascalCase` (`Weapon`, `InterestManager`, `StatusInstance`)
- Functions/methods: `snake_case` (`resolve_combat`, `register_kill`)
- Constants: `UPPER_SNAKE_CASE` (`ANNOYANCE_COST`, `CRAFTING_MATERIALS`, `W`)
- Private methods: `_leading_underscore` (`_drain`, `_resolve_sera_attack`)
- Internal tracking fields: `_leading_underscore` with `repr=False` in dataclasses

### Patterns

- **Deep copy before mutation**: Enemy lists and weapons are always `copy.deepcopy()`'d before combat or loot generation to avoid mutating templates
- **Log-returning functions**: Most game logic functions return `list[str]` log lines rather than printing directly
- **TYPE_CHECKING imports**: Forward references use `from typing import TYPE_CHECKING` with conditional imports to avoid circular dependencies
- **Condition strings**: Affix behavior is controlled by string keys evaluated at runtime, not hardcoded branching
- **Constants as class attributes**: `InterestManager` uses class-level constants like `TICK_DRAIN`, `KILL_RESTORE`, etc.

### UI Conventions

- All UI rendering goes through `sera/ui.py`
- Fixed box width: `W = 60` characters
- Box primitives: `box_top()`, `box_bot()`, `box_line()`, `box_blank()`, `box_divider()`
- HP/Patience bars use `#` (filled) and `-` (empty)
- Terminal clearing respects `TERM` environment variable

### Game Design Rules

- **Small numbers**: Base damage is 1-3. Final damage is clamped to 0-30. Scaling comes from affix synergies, not bigger numbers.
- **Transparency**: Every calculation step is shown. No hidden rolls (except dodge chance).
- **Sera's voice**: All flavor text and quips are written from Sera's perspective — imperious, bored, occasionally impressed by violence.
- **Enemy archetypes**: `trash` (HP ~8), `elite` (HP 25-30), `boss` (HP 40-50). Each has unique vulnerability gates.

## Testing

There is no automated test suite. Validation is done through:
- `main.py` — 3 scripted scenarios exercising the damage pipeline, permission system, and boss fights
- Manual playtesting via `play.py`

To verify changes haven't broken core logic, run:
```bash
python3 main.py
```
and confirm the 3 scenarios complete without errors and produce sensible output.

## Common Modification Tasks

### Adding a new weapon
1. Add entry to `data/weapons.json` with `name`, `base_damage` (1-3), `tags` (from `DamageTag` enum names), and `flavor`
2. The loader and encounter system will pick it up automatically

### Adding a new affix
1. Add entry to `data/affixes.json` with all fields (see existing entries for schema)
2. If the affix uses a new condition, add the condition handler in `combat.py`'s `_check_condition` function

### Adding a new enemy
1. Add entry to `data/enemies.json` following the archetype schema
2. Set `vulnerability` to an `EnemyVulnerability` enum name (or `"NONE"`)
3. Define abilities with `AnnoyanceType` enum names

### Adding a new damage tag
1. Add to `DamageTag` enum in `sera/tags.py`
2. Optionally add matching `EnemyVulnerability` entry
3. Update permission check logic in `combat.py` if needed

### Adding a new status effect
1. Add to `StatusEffect` enum in `sera/status.py`
2. If it deals DoT, add handling in `StatusInstance.tick_damage()`
3. Add combat resolver handling in `combat.py`

### Adding a new crafting material
1. Add to `CRAFTING_MATERIALS` dict in `sera/crafting.py`
2. Set `grants_tag` and optional `grants_prefix`/`grants_suffix`/`rename_to`

## Key Files for Understanding the Codebase

If you're new to the codebase, read in this order:
1. `sera/tags.py` — Enums that define the type system
2. `sera/status.py` — Status effect definitions
3. `sera/weapon.py` — Weapon and Affix dataclasses, damage pipeline
4. `sera/enemy.py` — Enemy class, annoyance types
5. `sera/interest.py` — Patience engine (the core mechanic)
6. `sera/combat.py` — How all the systems interact in a turn
7. `sera/loader.py` — How JSON data becomes game objects
8. `sera/encounters.py` — Encounter generation and loot
9. `main.py` — Scripted demos showing systems in action
10. `play.py` — Full interactive game loop
