"""Equipment models and random item generation."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field

from sera.stats import PlayerStats

SLOT_ORDER = [
    "Helmet",
    "Necklace",
    "Cloak",
    "Torso",
    "Ring 1",
    "Ring 2",
    "Legs",
    "Boots",
]

RANDOM_ABILITIES = [
    "Second Wind: +2 heal when using a flask.",
    "Thorns: attacker annoyance reduced by 1 once per turn.",
    "Arc Spark: +1 AP while above 70 Patience.",
    "Stone Skin: +1 Damage Reduction when below 40 Patience.",
    "Frost Veil: +10 Ice resistance.",
]


@dataclass
class EquipmentItem:
    name: str
    slot: str
    ascii_art: str = "[ ]"
    stat_bonuses: dict[str, int] = field(default_factory=dict)
    damage_reduction: int = 0
    damage_resistance: int = 0
    resistances: dict[str, int] = field(default_factory=dict)
    ability: str = ""


@dataclass
class EquipmentLoadout:
    equipped: dict[str, EquipmentItem | None] = field(default_factory=lambda: {slot: None for slot in SLOT_ORDER})

    def equip(self, item: EquipmentItem) -> EquipmentItem | None:
        old = self.equipped.get(item.slot)
        self.equipped[item.slot] = item
        return old

    def total_stat_bonuses(self) -> dict[str, int]:
        total: dict[str, int] = {}
        for item in self.equipped.values():
            if not item:
                continue
            for stat, value in item.stat_bonuses.items():
                total[stat] = total.get(stat, 0) + value
        return total

    def total_damage_reduction(self) -> int:
        return sum(item.damage_reduction for item in self.equipped.values() if item)

    def total_damage_resistance(self) -> int:
        return sum(item.damage_resistance for item in self.equipped.values() if item)

    def total_resistances(self) -> dict[str, int]:
        total: dict[str, int] = {}
        for item in self.equipped.values():
            if not item:
                continue
            for name, value in item.resistances.items():
                total[name] = total.get(name, 0) + value
        return total

    def build_final_stats(self, base: PlayerStats) -> PlayerStats:
        result = copy.deepcopy(base)
        result.add_flat(self.total_stat_bonuses())
        return result


def roll_item(template: EquipmentItem) -> EquipmentItem:
    item = copy.deepcopy(template)
    item.ability = random.choice(RANDOM_ABILITIES)

    # tiny random budget to keep numbers readable
    extra_stat = random.choice(["STR", "DEX", "CON", "WIS", "AC", "AP"])
    item.stat_bonuses[extra_stat] = item.stat_bonuses.get(extra_stat, 0) + random.choice([0, 1])
    if random.random() < 0.4:
        element = random.choice(["ice", "earth", "darkness", "fire", "water", "divine", "decay"])
        item.resistances[element] = item.resistances.get(element, 0) + random.choice([5, 10])
    return item
