# AGENTS.md — Codex Development Guide

## Quick Start

```bash
# Run the game
python3 play.py

# Run simulation scenarios (validates core logic)
python3 main.py

# Verify nothing is broken after changes
python3 -c "from main import run_scenario_1, run_scenario_2, run_scenario_3; run_scenario_1(verbose=False); run_scenario_2(verbose=False); run_scenario_3(verbose=False); print('OK')"
```

**No dependencies. No build step. No virtual environment.** Standard library only.

## Verification

After ANY code change, run:

```bash
python3 main.py
```

All 3 scenarios must complete without errors. Check the output makes sense (damage numbers, patience changes, kill counts).

For targeted validation:

```bash
# Test just the imports and data loading
python3 -c "from sera.loader import load_weapons, load_enemies, load_affixes; print(len(load_weapons()), 'weapons', len(load_enemies()), 'enemies', len(load_affixes()), 'affixes')"

# Test the UI renders
python3 -c "from sera import ui; print(ui.render_title_screen())"

# Test a single scenario silently
python3 -c "from main import run_scenario_1; r = run_scenario_1(verbose=False); print(r['name'], r['kills'], r['patience'])"
```

## Architecture Overview

```
play.py          ← Interactive game (entry point for players)
main.py          ← Scripted demos (entry point for testing)
sera/            ← Core engine
  tags.py        ← Enums: DamageTag, EnemyVulnerability
  status.py      ← StatusEffect enum, StatusInstance dataclass
  weapon.py      ← Weapon + Affix dataclasses, damage pipeline
  enemy.py       ← Enemy class, abilities, AI
  interest.py    ← InterestManager (Patience = Sera's HP)
  combat.py      ← Combat resolver (turn loop)
  crafting.py    ← CraftingMaterial, apply_material()
  loader.py      ← JSON → game objects
  encounters.py  ← Floor encounter generation, loot drops
  ui.py          ← All ASCII rendering + pixel UI overlay system
data/            ← JSON content files
  weapons.json   ← 10 base weapons
  affixes.json   ← 10 prefix/suffix definitions
  enemies.json   ← 5 enemy archetypes
```

## Key Patterns

### Data flows one direction: JSON → loader → game objects → combat → log output

All game content (weapons, enemies, affixes) is defined in `data/*.json` and loaded by `sera/loader.py`. Combat functions return `list[str]` log lines or `CombatResult` dataclasses. The UI layer in `sera/ui.py` renders everything.

### Damage Pipeline (weapon.py)

```
base_damage → +flat bonuses (conditional) → ×multipliers (conditional) → +per-stack bonuses → clamp [0,30]
```

Each step is logged in `list[str]` for transparent display.

### Condition System

Affix effects are gated by string condition keys resolved in `weapon.py:_check_condition()`:
- `"always"`, `"enemy_full_hp"`, `"enemy_below_half"`, `"enemy_casting"`, `"enemy_has_debuffs"`, `"first_hit"`

To add a new condition: add a branch in `_check_condition()`.

### Permission System (tags.py + enemy.py)

Enemies have `EnemyVulnerability` (e.g. `REQUIRES_DIVINE`). Weapons need matching `DamageTag` to deal damage. Wrong tag = 0 damage + patience penalty.

### Deep Copy Convention

Always `copy.deepcopy()` enemies and weapons before combat or loot generation. Templates in the loaded pools must never be mutated.

## Common Tasks

### Add a new weapon
1. Add entry to `data/weapons.json` with `name`, `base_damage` (1-3), `tags`, `flavor`
2. Run `python3 main.py` to verify

### Add a new enemy
1. Add entry to `data/enemies.json` with `name`, `max_hp`, `archetype` (trash/elite/boss), `vulnerability`, `abilities`
2. Run `python3 main.py` to verify

### Add a new affix
1. Add entry to `data/affixes.json`
2. If it uses a new condition string, add handler in `weapon.py:_check_condition()`

### Add a new damage tag
1. Add to `DamageTag` enum in `sera/tags.py`
2. Optionally add matching `EnemyVulnerability`
3. Update `enemy.py:check_permission()` tag_map if needed

### Add a new status effect
1. Add to `StatusEffect` enum in `sera/status.py`
2. If it deals DoT, add handling in `StatusInstance.tick_damage()`
3. Add quip in `combat.py:_status_quip()`

### Add a new crafting material
1. Add to `CRAFTING_MATERIALS` dict in `sera/crafting.py`

### Add a new UI screen
1. Add a `render_*` function in `sera/ui.py` using box primitives: `box_top()`, `box_bot()`, `box_line()`, `box_blank()`, `box_divider()`
2. Box width is always `W = 60`
3. Call it from `play.py`

### Add a new simulation scenario
1. Add a `run_scenario_N(verbose=True) -> dict` function in `main.py`
2. Return dict with keys: `name`, `kills`, `patience`, `max_patience`, `turns`, `game_over`, `log`
3. Add it to the `results` list in `play.py:run_simulation()`

### Add to the between-floors menu
1. Add option to `sera/ui.py:render_between_floors()`
2. Add handler in `play.py:between_floors()` with matching choice number
3. Update the valid choices list

## File-by-File Reference

| File | What to know |
|------|-------------|
| `sera/tags.py` | Pure enums. No logic. Change here first when adding new damage types. |
| `sera/status.py` | `StatusEffect` enum + `StatusInstance` dataclass. DoT logic in `tick_damage()`. |
| `sera/weapon.py` | `Weapon.calculate_damage()` is the damage pipeline. `_check_condition()` resolves affix gates. |
| `sera/enemy.py` | `Enemy.choose_action()` is the AI. `take_damage()` applies armor. `check_permission()` gates damage. |
| `sera/interest.py` | `InterestManager` is Patience. `register_kill()` handles kill/overkill/multi-kill bonuses. |
| `sera/combat.py` | `resolve_combat()` runs the automated turn loop. Returns `CombatResult`. |
| `sera/crafting.py` | `apply_material()` modifies a weapon in-place. `CRAFTING_MATERIALS` is the material registry. |
| `sera/loader.py` | `load_weapons()`, `load_enemies()`, `load_affixes()` parse JSON into game objects. |
| `sera/encounters.py` | `generate_encounter()` builds enemy groups by floor. `generate_loot_weapon()` creates drops. |
| `sera/ui.py` | All rendering. Box primitives + composite screen renderers. Also has pixel UI overlay classes. |
| `play.py` | Interactive game loop. `GameState`, `RunStats`, combat input handling, simulation mode, menus. |
| `main.py` | 3 scripted scenarios. Each returns structured dict. Can run verbose (standalone) or silent (UI). |

## Style Rules

- Python 3.10+ (`X | None` union syntax, `from __future__ import annotations`)
- `@dataclass` for all data containers
- `Enum` with `auto()` for all type enums
- Functions return `list[str]` logs, not print directly
- Deep copy before mutation
- Constants as `UPPER_SNAKE_CASE`
- Section separators: `# ─────────` comment blocks
- No external dependencies

## Sera's Voice

All flavor text must be written in Sera's voice: first person, present tense, short sentences, contemptuous, never enthusiastic (except for overkill). See `CLAUDE.md` for the full character bible. Key rules:
- "Die faster." not "She told them to die faster."
- No emojis, no exclamation marks (except overkill)
- Contempt is default. Highest praise is "...Acceptable."
