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

# Every incoming attack channel has a matching defense key.
DEFENSE_TYPES = [
    "generic",
    "physical",
    "fire",
    "ice",
    "water",
    "earth",
    "divine",
    "darkness",
    "decay",
    "arcane",
    "sonic",
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
    level: int = 1
    is_unique: bool = False
    set_name: str = ""
    is_named: bool = False

    @property
    def max_level(self) -> int:
        if self.is_unique or self.is_named or self.set_name:
            return 10
        return 5

    @property
    def can_upgrade(self) -> bool:
        return self.level < self.max_level

    @property
    def upgrade_cost(self) -> int:
        return self.level


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
        total: dict[str, int] = {k: 0 for k in DEFENSE_TYPES}
        for item in self.equipped.values():
            if not item:
                continue
            for name, value in item.resistances.items():
                key = normalize_defense_key(name)
                total[key] = total.get(key, 0) + value
        return total

    def build_final_stats(self, base: PlayerStats) -> PlayerStats:
        result = copy.deepcopy(base)
        result.add_flat(self.total_stat_bonuses())
        return result


def normalize_defense_key(value: str) -> str:
    key = (value or "generic").strip().lower()
    if key in DEFENSE_TYPES:
        return key
    if key == "dark":
        return "darkness"
    return "generic"


def infuse_item(item: EquipmentItem, stat: str | None = None, defense_type: str | None = None) -> EquipmentItem:
    """Small-number upgrade path for armor/rings/cloaks/etc."""
    upgraded = copy.deepcopy(item)
    if stat:
        upgraded.stat_bonuses[stat] = upgraded.stat_bonuses.get(stat, 0) + 1
    if defense_type:
        key = normalize_defense_key(defense_type)
        upgraded.resistances[key] = upgraded.resistances.get(key, 0) + 5
    return upgraded


def upgrade_equipment(item: EquipmentItem, shards_available: int) -> tuple[list[str], int]:
    log: list[str] = []
    if not item.can_upgrade:
        log.append(f"  {item.name} is max level ({item.max_level}).")
        return log, 0

    cost = item.upgrade_cost
    if shards_available < cost:
        log.append(f"  Need {cost} shards, have {shards_available}.")
        return log, 0

    item.level += 1
    item.damage_reduction += 1 if item.level % 2 == 0 else 0
    item.damage_resistance += 1
    for stat in list(item.stat_bonuses):
        if random.random() < 0.5:
            item.stat_bonuses[stat] += 1
    log.append(f"  {item.name} upgraded to Lv {item.level}/{item.max_level}.")
    log.append(f"  Cost: {cost} shards.")
    return log, cost


def roll_item(template: EquipmentItem) -> EquipmentItem:
    item = copy.deepcopy(template)
    item.ability = random.choice(RANDOM_ABILITIES)

    # tiny random budget to keep numbers readable
    extra_stat = random.choice(["STR", "DEX", "CON", "WIS", "AC", "AP"])
    item.stat_bonuses[extra_stat] = item.stat_bonuses.get(extra_stat, 0) + random.choice([0, 1])
    if random.random() < 0.4:
        element = random.choice(DEFENSE_TYPES[1:])
        item.resistances[element] = item.resistances.get(element, 0) + random.choice([5, 10])
    return item


def generate_revision_set(all_equipment: list[EquipmentItem], floor: int) -> list[EquipmentItem]:
    """Create a complete next-revision kit: one item per slot with light infusion."""
    by_slot: dict[str, list[EquipmentItem]] = {slot: [] for slot in SLOT_ORDER}
    for item in all_equipment:
        if item.slot in by_slot:
            by_slot[item.slot].append(item)

    preferred = ["physical", "fire", "ice", "arcane", "divine", "darkness"]
    kit: list[EquipmentItem] = []
    for i, slot in enumerate(SLOT_ORDER):
        choices = by_slot.get(slot, [])
        if not choices:
            continue
        base = copy.deepcopy(random.choice(choices))
        defense_choice = preferred[(floor + i) % len(preferred)]
        stat_choice = random.choice(["STR", "DEX", "CON", "WIS", "AC", "AP"])
        kit.append(infuse_item(base, stat=stat_choice if floor >= 2 else None, defense_type=defense_choice))
    return kit
