"""
Encounter generator — builds rooms of enemies for the dungeon run.

Pulls from the JSON archetypes and scales encounters across floors.
"""

from __future__ import annotations
import copy
import random
from collections import Counter

from sera.loader import load_enemies, load_weapons, load_affixes
from sera.weapon import Weapon, Affix
from sera.enemy import Enemy
from sera.crafting import CraftingMaterial, CRAFTING_MATERIALS
from sera.randomization import RunRNG, select_wave_enemies


def _disambiguate_names(enemies: list[Enemy]) -> None:
    """Add A/B/C suffixes when multiple enemies share a name."""
    name_counts = Counter(e.name for e in enemies)
    name_seen: dict[str, int] = {}
    for e in enemies:
        if name_counts[e.name] > 1:
            idx = name_seen.get(e.name, 0)
            suffix = chr(ord("A") + idx)
            name_seen[e.name] = idx + 1
            e.name = f"{e.name} {suffix}"


def _scale_enemy(enemy: Enemy, floor: int) -> None:
    """Scale enemy stats based on floor. Keeps small-number feel."""
    # Add a random dodge chance (0-15%) if enemy doesn't already have one
    if enemy.dodge_chance == 0.0 and random.random() < 0.4:
        enemy.dodge_chance = random.uniform(0.05, 0.15)

    if floor <= 1:
        return
    # +15% HP per floor past 1 — keeps the small-number feel intact
    bonus_hp = int(enemy.max_hp * 0.15 * (floor - 1))
    enemy.max_hp += bonus_hp
    enemy.current_hp = enemy.max_hp
    # +1 armor every 3 floors for armored enemies
    if enemy.armor > 0 and floor >= 3:
        enemy.armor += (floor - 1) // 2
    # Slightly increase dodge chance on higher floors
    if enemy.dodge_chance > 0.0 and floor >= 3:
        enemy.dodge_chance = min(0.30, enemy.dodge_chance + (floor - 1) * 0.02)


def generate_encounter(floor: int, all_enemies: list[Enemy], rng: RunRNG | None = None) -> list[Enemy]:
    """
    Build an encounter for the given floor number.

    Floor 1:   1 trash (tutorial)
    Floor 2:   2 trash
    Floor 3-4: 1 elite or 2-3 trash
    Floor 5:   Boss + 1 trash escort
    Floor 6+:  Escalate (boss + elite, etc.)
    """
    trash = [e for e in all_enemies if e.archetype == "trash"]
    elites = [e for e in all_enemies if e.archetype == "elite"]
    bosses = [e for e in all_enemies if e.archetype == "boss"]
    rand = rng._rng if rng else random

    if floor == 1:
        pool = trash if trash else all_enemies
        picks = [copy.deepcopy(rand.choice(pool))]
    elif floor == 2:
        pool = trash if trash else all_enemies
        picks = [copy.deepcopy(rand.choice(pool)) for _ in range(2)]
    elif floor <= 4:
        if elites and rand.random() < 0.6:
            picks = [copy.deepcopy(rand.choice(elites))]
        else:
            count = rand.randint(2, 3)
            pool = trash if trash else all_enemies
            picks = [copy.deepcopy(rand.choice(pool)) for _ in range(count)]
    elif floor == 5:
        boss = copy.deepcopy(rand.choice(bosses)) if bosses else copy.deepcopy(rand.choice(elites))
        escort = copy.deepcopy(rand.choice(trash)) if trash else None
        picks = [boss] + ([escort] if escort else [])
    else:
        boss = copy.deepcopy(rand.choice(bosses)) if bosses else copy.deepcopy(rand.choice(elites))
        extra = copy.deepcopy(rand.choice(elites)) if elites else copy.deepcopy(rand.choice(trash))
        picks = [boss, extra]

    # Scale and disambiguate
    for e in picks:
        _scale_enemy(e, floor)
    _disambiguate_names(picks)

    return picks


def generate_loot_weapon(floor: int, all_weapons: list[Weapon], all_affixes: list[Affix]) -> Weapon:
    """Generate a weapon drop with random affixes based on floor."""
    base = copy.deepcopy(random.choice(all_weapons))

    prefixes = [a for a in all_affixes if a.affix_type == "prefix"]
    suffixes = [a for a in all_affixes if a.affix_type == "suffix"]

    # Higher floors = more likely to have affixes
    if prefixes and random.random() < min(0.3 + floor * 0.1, 0.8):
        base.prefix = copy.deepcopy(random.choice(prefixes))
    if suffixes and random.random() < min(0.2 + floor * 0.1, 0.7):
        base.suffix = copy.deepcopy(random.choice(suffixes))

    return base


def generate_loot_material() -> CraftingMaterial | None:
    """Random chance to find a crafting material (65% — players need options to fix immunity gates)."""
    if random.random() < 0.65:
        return copy.deepcopy(random.choice(list(CRAFTING_MATERIALS.values())))
    return None


def generate_loot_shards(floor: int) -> int:
    """
    Generate upgrade shards as loot. Higher floors = more shards.

    Floor 1: 0-1 shards (50% chance)
    Floor 2: 0-1 shards (60% chance)
    Floor 3: 1-2 shards (70% chance)
    Floor 4: 1-2 shards (80% chance)
    Floor 5: 2-3 shards (guaranteed)
    """
    chance = min(0.5 + floor * 0.1, 1.0)
    if random.random() > chance:
        return 0
    if floor <= 2:
        return random.randint(0, 1) or 1  # at least 1 if we passed the check
    if floor <= 4:
        return random.randint(1, 2)
    return random.randint(2, 3)
