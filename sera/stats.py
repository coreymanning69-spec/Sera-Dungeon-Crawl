"""Player stat system for SERA."""

from __future__ import annotations

from dataclasses import dataclass, field


CORE_STAT_ORDER = ["STR", "DEX", "CON", "WIS", "AC", "AP", "INT", "LUK"]


@dataclass
class PlayerStats:
    """Small-number RPG stats used by combat and equipment."""

    values: dict[str, int] = field(default_factory=lambda: {
        "STR": 3,
        "DEX": 3,
        "CON": 3,
        "WIS": 3,
        "AC": 2,
        "AP": 2,
        "INT": 2,
        "LUK": 2,
    })

    def get(self, key: str) -> int:
        return self.values.get(key, 0)

    def add_flat(self, bonuses: dict[str, int]):
        for key, value in bonuses.items():
            self.values[key] = self.get(key) + value

    def attack_bonus(self) -> int:
        return self.get("STR") // 2 + self.get("AP")

    def annoyance_reduction(self) -> int:
        return self.get("AC") // 2 + self.get("DEX") // 4

    def healing_power(self) -> int:
        return 6 + self.get("WIS") + self.get("CON") // 2

    def as_lines(self) -> list[str]:
        return [f"{k}: {self.get(k)}" for k in CORE_STAT_ORDER]
