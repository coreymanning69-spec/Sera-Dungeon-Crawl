"""
Encounter generator — builds rooms of enemies for the dungeon run.

Pulls from the JSON archetypes and scales encounters across floors.
"""

from __future__ import annotations
import copy
import random

from sera.loader import load_enemies, load_weapons, load_affixes
from sera.weapon import Weapon, Affix
from sera.enemy import Enemy
from sera.crafting import CraftingMaterial, CRAFTING_MATERIALS


def generate_encounter(floor: int, all_enemies: list[Enemy]) -> list[Enemy]:
    """
    Build an encounter for the given floor number.

    Floor 1-2: 1-2 trash mobs
    Floor 3-4: 1 elite or 2-3 trash
    Floor 5:   Boss + 1 trash escort
    Floor 6+:  Escalate (boss + elite, etc.)
    """
    trash = [e for e in all_enemies if e.archetype == "trash"]
    elites = [e for e in all_enemies if e.archetype == "elite"]
    bosses = [e for e in all_enemies if e.archetype == "boss"]

    if floor <= 2:
        count = random.randint(1, 2)
        pool = trash if trash else all_enemies
        picks = [copy.deepcopy(random.choice(pool)) for _ in range(count)]
    elif floor <= 4:
        if elites and random.random() < 0.6:
            picks = [copy.deepcopy(random.choice(elites))]
        else:
            count = random.randint(2, 3)
            pool = trash if trash else all_enemies
            picks = [copy.deepcopy(random.choice(pool)) for _ in range(count)]
    elif floor == 5:
        boss = copy.deepcopy(random.choice(bosses)) if bosses else copy.deepcopy(random.choice(elites))
        escort = copy.deepcopy(random.choice(trash)) if trash else None
        picks = [boss] + ([escort] if escort else [])
    else:
        boss = copy.deepcopy(random.choice(bosses)) if bosses else copy.deepcopy(random.choice(elites))
        extra = copy.deepcopy(random.choice(elites)) if elites else copy.deepcopy(random.choice(trash))
        picks = [boss, extra]

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
    """Random chance to find a crafting material."""
    if random.random() < 0.4:
        return copy.deepcopy(random.choice(list(CRAFTING_MATERIALS.values())))
    return None
