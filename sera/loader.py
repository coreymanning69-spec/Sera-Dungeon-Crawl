"""
Data loader — reads JSON content into live game objects.
"""

from __future__ import annotations
import json
from pathlib import Path

from sera.tags import DamageTag, EnemyVulnerability
from sera.weapon import Weapon, Affix
from sera.enemy import Enemy, EnemyAbility, AnnoyanceType


DATA_DIR = Path(__file__).parent.parent / "data"


def load_weapons() -> list[Weapon]:
    with open(DATA_DIR / "weapons.json") as f:
        data = json.load(f)
    weapons = []
    for w in data["base_weapons"]:
        tags = [DamageTag[t] for t in w["tags"]]
        weapons.append(Weapon(
            name=w["name"],
            base_damage=w["base_damage"],
            tags=tags,
            flavor=w["flavor"],
        ))
    return weapons


def load_affixes() -> list[Affix]:
    with open(DATA_DIR / "affixes.json") as f:
        data = json.load(f)
    affixes = []
    for a in data["affixes"]:
        granted = DamageTag[a["granted_tag"]] if a["granted_tag"] else None
        affixes.append(Affix(
            name=a["name"],
            description=a["description"],
            affix_type=a["affix_type"],
            flat_bonus=a["flat_bonus"],
            flat_condition=a["flat_condition"],
            multiplier=a["multiplier"],
            mult_condition=a["mult_condition"],
            per_stack_bonus=a["per_stack_bonus"],
            per_stack_source=a["per_stack_source"],
            granted_tag=granted,
            inflicts_status=a["inflicts_status"],
            status_duration=a["status_duration"],
            status_potency=a["status_potency"],
        ))
    return affixes


def load_enemies() -> list[Enemy]:
    with open(DATA_DIR / "enemies.json") as f:
        data = json.load(f)
    enemies = []
    for e in data["enemy_archetypes"]:
        vuln = EnemyVulnerability[e["vulnerability"]] if e["vulnerability"] != "NONE" else EnemyVulnerability.NONE
        abilities = []
        for ab in e["abilities"]:
            abilities.append(EnemyAbility(
                name=ab["name"],
                annoyance=AnnoyanceType[ab["annoyance"]],
                cooldown=ab["cooldown"],
                charge_time=ab["charge_time"],
                flavor=ab["flavor"],
            ))
        weaknesses = [DamageTag[tag] for tag in e.get("elemental_weaknesses", [])]
        resistances = [DamageTag[tag] for tag in e.get("elemental_resistances", [])]
        enemies.append(Enemy(
            name=e["name"],
            max_hp=e["max_hp"],
            archetype=e["archetype"],
            vulnerability=vuln,
            abilities=abilities,
            armor=e["armor"],
            regen_per_turn=e["regen_per_turn"],
            dodge_chance=e["dodge_chance"],
            elemental_weaknesses=weaknesses,
            elemental_resistances=resistances,
            flavor=e["flavor"],
        ))
    return enemies


def get_affix_by_name(name: str, affixes: list[Affix] | None = None) -> Affix | None:
    if affixes is None:
        affixes = load_affixes()
    for a in affixes:
        if a.name == name:
            return a
    return None
