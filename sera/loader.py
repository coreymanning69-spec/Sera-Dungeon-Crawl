"""
Data loader — reads JSON content into live game objects.
"""

from __future__ import annotations
import json
from pathlib import Path

from sera.tags import DamageTag, EnemyVulnerability
from sera.weapon import Weapon, Affix
from sera.enemy import Enemy, EnemyAbility, AnnoyanceType, normalize_attack_type
from sera.equipment import EquipmentItem, normalize_defense_key


DATA_DIR = Path(__file__).parent.parent / "data"


CULTIST_QUIPS = [
    "For the glory of the Queen!",
    "The hoard grows!",
    "You will make a fine sacrifice.",
]

GUARD_QUIPS = [
    "Hold the line! Greenest will not fall!",
    "Keep them away from the keep!",
    "By Chauntea, there are too many of them!",
]



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
                attack_type=normalize_attack_type(ab.get("attack_type", "generic")),
            ))
        elem_weak = [DamageTag[t] for t in e.get("elemental_weaknesses", [])]
        elem_resist = [DamageTag[t] for t in e.get("elemental_resistances", [])]
        enemies.append(Enemy(
            name=e["name"],
            max_hp=e["max_hp"],
            archetype=e["archetype"],
            vulnerability=vuln,
            abilities=abilities,
            armor=e["armor"],
            regen_per_turn=e["regen_per_turn"],
            dodge_chance=e["dodge_chance"],
            flavor=e["flavor"],
            elemental_weaknesses=elem_weak,
            elemental_resistances=elem_resist,
        ))
    return enemies


def load_equipment_items() -> list[EquipmentItem]:
    with open(DATA_DIR / "equipment_items.json") as f:
        data = json.load(f)
    items = []
    for item in data["equipment_items"]:
        items.append(EquipmentItem(
            name=item["name"],
            slot=item["slot"],
            ascii_art=item.get("ascii_art", "[ ]"),
            stat_bonuses=item.get("stat_bonuses", {}),
            damage_reduction=item.get("damage_reduction", 0),
            damage_resistance=item.get("damage_resistance", 0),
            resistances={normalize_defense_key(k): v for k, v in item.get("resistances", {}).items()},
            level=item.get("level", 1),
            is_unique=item.get("is_unique", False),
            set_name=item.get("set_name", ""),
            is_named=item.get("is_named", False),
        ))
    return items


def get_affix_by_name(name: str, affixes: list[Affix] | None = None) -> Affix | None:
    if affixes is None:
        affixes = load_affixes()
    for a in affixes:
        if a.name == name:
            return a
    return None
