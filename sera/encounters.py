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
from sera.enemy import Enemy, EnemyAbility, AnnoyanceType
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


def _scale_enemy(enemy: Enemy, floor: int, rand=random) -> None:
    """Scale enemy stats based on floor. Keeps small-number feel."""
    # Add a random dodge chance (0-15%) if enemy doesn't already have one
    if enemy.dodge_chance == 0.0 and rand.random() < 0.4:
        enemy.dodge_chance = rand.uniform(0.05, 0.15)

    if floor <= 1:
        return
    # +10% HP per floor past 1 for smoother baseline progression
    bonus_hp = int(enemy.max_hp * 0.10 * (floor - 1))
    enemy.max_hp += bonus_hp
    enemy.current_hp = enemy.max_hp
    # +1 armor every 3 floors for armored enemies
    if enemy.armor > 0 and floor >= 3:
        enemy.armor += (floor - 1) // 2
    # Slightly increase dodge chance on higher floors
    if enemy.dodge_chance > 0.0 and floor >= 3:
        enemy.dodge_chance = min(0.24, enemy.dodge_chance + (floor - 1) * 0.012)


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
        _scale_enemy(e, floor, rand)
        _roll_boss_mutator(e, floor, rand)
    _disambiguate_names(picks)

    return picks




BOSS_MUTATOR_POOL = [
    {
        "name": "Warcaller",
        "ability": {
            "name": "Working Reinforcements",
            "annoyance": AnnoyanceType.SUMMON,
            "cooldown": 3,
            "charge_time": 1,
            "flavor": "Reinforcements arrive. I hate that this one actually works.",
            "attack_type": "sonic",
        },
    },
    {
        "name": "Aegis-Bound",
        "ability": {
            "name": "Null Ward",
            "annoyance": AnnoyanceType.STUN,
            "cooldown": 4,
            "charge_time": 0,
            "flavor": "I phase through your opening strike.",
            "attack_type": "arcane",
        },
    },
]

BOSS_MUTATORS: dict[str, dict[str, float | str]] = {
    "Draconic Resilience": {
        "description": "At 50% HP, cleanses debuffs and doubles armor for 2 turns.",
        "trigger_threshold": 0.5,
        "effect": "cleanse_and_fortify",
        "weight": 0.6,
    },
    "Acidic Blood": {
        "description": "Deals minor acid splash damage to the player upon receiving a melee critical hit.",
        "trigger_event": "on_receive_crit",
        "effect": "acid_splash_damage",
        "weight": 0.4,
    },
}


def _weighted_boss_mutator_roll(rand=random) -> dict[str, float | str]:
    pool = list(BOSS_MUTATORS.items())
    total = sum(float(data.get("weight", 1.0)) for _, data in pool)
    pick = rand.uniform(0.0, total)
    cursor = 0.0
    for name, data in pool:
        cursor += float(data.get("weight", 1.0))
        if pick <= cursor:
            rolled = copy.deepcopy(data)
            rolled["name"] = name
            return rolled
    fallback_name, fallback = pool[-1]
    rolled = copy.deepcopy(fallback)
    rolled["name"] = fallback_name
    return rolled


def _roll_boss_mutator(enemy: Enemy, floor: int, rand=random) -> None:
    """Small weighted chance for bosses to spawn with a named mutator ability."""
    if enemy.archetype != "boss":
        return
    chance = min(0.08 + floor * 0.01, 0.18)
    if rand.random() > chance:
        return
    mutator = copy.deepcopy(rand.choice(BOSS_MUTATOR_POOL))
    enemy.name = f"{mutator['name']} {enemy.name}"
    ab = mutator["ability"]
    enemy.abilities.append(EnemyAbility(
        name=ab["name"],
        annoyance=ab["annoyance"],
        cooldown=ab["cooldown"],
        charge_time=ab["charge_time"],
        flavor=ab["flavor"],
        attack_type=ab["attack_type"],
    ))

    # Separate named boss mutator profile (used by combat hooks).
    named_chance = min(0.22 + floor * 0.015, 0.45)
    if rand.random() <= named_chance:
        rolled = _weighted_boss_mutator_roll(rand)
        existing = getattr(enemy, "boss_mutators", [])
        existing.append(rolled)
        setattr(enemy, "boss_mutators", existing)

def _scale_endless_enemy(enemy: Enemy, wave: int, pressure: int, rand=random) -> None:
    """Apply endless-mode scaling pressure to a copied enemy."""
    _scale_enemy(enemy, wave, rand)

    hp_mult = 1.0 + (0.10 * max(0, wave - 1)) + (0.02 * max(0, wave - 10))
    enemy.max_hp = max(enemy.max_hp, int(round(enemy.max_hp * hp_mult)))
    enemy.current_hp = enemy.max_hp

    armor_bonus = wave // 4
    if enemy.archetype == "elite":
        armor_bonus += wave // 8
    if enemy.archetype == "boss":
        armor_bonus += wave // 6
    enemy.armor += armor_bonus

    enemy.dodge_chance = min(0.35, enemy.dodge_chance + (0.01 * max(0, wave - 1)))
    if wave >= 8 and enemy.archetype in {"elite", "boss"}:
        enemy.regen_per_turn += max(1, wave // 10)

    for ability in enemy.abilities:
        ability.cooldown = max(0, ability.cooldown - pressure)
        if ability.charge_time > 1:
            ability.charge_time = max(1, ability.charge_time - (pressure // 2))


def generate_endless_encounter(wave: int, all_enemies: list[Enemy], rng: RunRNG | None = None) -> list[Enemy]:
    """Build endless-mode encounters with wave-based HP/armor/ability pressure."""
    trash = [e for e in all_enemies if e.archetype == "trash"]
    elites = [e for e in all_enemies if e.archetype == "elite"]
    bosses = [e for e in all_enemies if e.archetype == "boss"]
    rand = rng._rng if rng else random

    pressure = max(0, (wave - 1) // 6)
    picks: list[Enemy] = []

    if wave <= 2:
        count = 1 if wave == 1 else 2
        pool = trash if trash else all_enemies
        picks = [copy.deepcopy(rand.choice(pool)) for _ in range(count)]
    elif wave <= 5:
        pool = trash if trash else all_enemies
        picks = [copy.deepcopy(rand.choice(pool)) for _ in range(rand.randint(2, 3))]
        if elites and rand.random() < 0.65:
            picks.append(copy.deepcopy(rand.choice(elites)))
    elif wave <= 9:
        if elites:
            picks.append(copy.deepcopy(rand.choice(elites)))
        pool = trash if trash else all_enemies
        picks.extend(copy.deepcopy(rand.choice(pool)) for _ in range(rand.randint(1, 2)))
    else:
        if bosses and wave % 3 == 0:
            picks.append(copy.deepcopy(rand.choice(bosses)))
        elif elites:
            picks.append(copy.deepcopy(rand.choice(elites)))

        if elites and wave >= 12:
            picks.append(copy.deepcopy(rand.choice(elites)))
        pool = trash if trash else all_enemies
        extras = 1 + min(2, wave // 10)
        picks.extend(copy.deepcopy(rand.choice(pool)) for _ in range(extras))

    for enemy in picks:
        _scale_endless_enemy(enemy, wave, pressure, rand)
        _roll_boss_mutator(enemy, wave, rand)
    _disambiguate_names(picks)
    return picks


def generate_loot_weapon(floor: int, all_weapons: list[Weapon], all_affixes: list[Affix]) -> Weapon:
    """Generate a weapon drop with random affixes based on floor."""
    base = copy.deepcopy(random.choice(all_weapons))

    prefixes = [a for a in all_affixes if a.affix_type == "prefix"]
    suffixes = [a for a in all_affixes if a.affix_type == "suffix"]

    # Higher floors = more likely to have affixes
    if prefixes and random.random() < min(0.45 + floor * 0.11, 0.92):
        base.prefix = copy.deepcopy(random.choice(prefixes))
    if suffixes and random.random() < min(0.4 + floor * 0.11, 0.9):
        base.suffix = copy.deepcopy(random.choice(suffixes))

    return base


def generate_loot_material() -> CraftingMaterial | None:
    """Random chance to find a crafting material (80% for smoother progression)."""
    if random.random() < 0.80:
        return copy.deepcopy(random.choice(list(CRAFTING_MATERIALS.values())))
    return None


def generate_loot_shards(floor: int) -> int:
    """Generate upgrade shards with weighted 1/2/3 outcomes."""
    chance = min(0.60 + floor * 0.12, 0.98)
    if random.random() > chance:
        return 0

    # weighted payout biased by floor progression
    if floor <= 2:
        return random.choices([1, 2, 3], weights=[75, 20, 5], k=1)[0]
    if floor <= 4:
        return random.choices([1, 2, 3], weights=[45, 40, 15], k=1)[0]
    return random.choices([1, 2, 3], weights=[25, 45, 30], k=1)[0]
