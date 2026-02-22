"""Weapon customization pools for base, procedural, and legendary item sources."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from sera.weapon import Weapon, Affix
from sera.randomization import RunRNG


@dataclass
class LegendaryWeaponProgress:
    weapon_name: str
    level: int = 1
    xp: int = 0

    def grant_xp(self, amount: int) -> None:
        self.xp += max(0, amount)
        while self.xp >= self.level * 3:
            self.xp -= self.level * 3
            self.level += 1


@dataclass
class WeaponPoolManager:
    base_pool: list[Weapon]
    affix_pool: list[Affix]
    rng: RunRNG
    legendary_pool: list[Weapon] = field(default_factory=list)
    legendary_progress: dict[str, LegendaryWeaponProgress] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.legendary_pool and self.base_pool:
            for template in self.base_pool[:3]:
                legendary = copy.deepcopy(template)
                legendary.name = f"{template.name} Prime"
                legendary.base_damage = min(3, legendary.base_damage + 1)
                legendary.is_unique = True
                self.legendary_pool.append(legendary)
                self.legendary_progress[legendary.name] = LegendaryWeaponProgress(legendary.name)

    def generate_starting_weapon(self) -> Weapon:
        return copy.deepcopy(self.rng.choice(self.base_pool))

    def _procedural_weapon(self) -> Weapon:
        weapon = copy.deepcopy(self.rng.choice(self.base_pool))
        prefixes = [a for a in self.affix_pool if a.affix_type == "prefix"]
        suffixes = [a for a in self.affix_pool if a.affix_type == "suffix"]
        if prefixes and self.rng.random() < 0.7:
            weapon.prefix = copy.deepcopy(self.rng.choice(prefixes))
        if suffixes and self.rng.random() < 0.7:
            weapon.suffix = copy.deepcopy(self.rng.choice(suffixes))

        extra_pool = [a for a in self.affix_pool if a.affix_type in {"prefix", "suffix"}]
        while weapon.can_add_modifier and extra_pool and self.rng.random() < 0.35:
            weapon.add_modifier(copy.deepcopy(self.rng.choice(extra_pool)))
        return weapon

    def _legendary_weapon(self) -> Weapon:
        weapon = copy.deepcopy(self.rng.choice(self.legendary_pool))
        progress = self.legendary_progress[weapon.name]
        weapon.upgrade_level = min(progress.level - 1, weapon.max_upgrade_level)
        progress.grant_xp(1)
        return weapon

    def generate_drop(self, floor: int) -> Weapon:
        if floor >= 8 and self.legendary_pool and self.rng.random() < 0.2:
            return self._legendary_weapon()
        if self.rng.random() < min(0.35 + floor * 0.05, 0.9):
            return self._procedural_weapon()
        return copy.deepcopy(self.rng.choice(self.base_pool))
