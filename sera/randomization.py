"""Deterministic randomization helpers for encounter and weapon selection."""

from __future__ import annotations
import random

from sera.enemy import Enemy
from sera.weapon import Weapon


class RunRNG:
    def __init__(self, seed: int):
        self.seed = seed
        self._rng = random.Random(seed)

    def choice(self, values: list):
        return self._rng.choice(values)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def random(self) -> float:
        return self._rng.random()

    def shuffle(self, values: list) -> None:
        self._rng.shuffle(values)


def select_weapon_choices(all_weapons: list[Weapon], count: int, rng: RunRNG) -> list[Weapon]:
    pool = list(all_weapons)
    rng.shuffle(pool)
    return pool[:count]


def select_wave_enemies(all_enemies: list[Enemy], count: int, rng: RunRNG) -> list[Enemy]:
    picks: list[Enemy] = []
    if not all_enemies:
        return picks
    for _ in range(count):
        picks.append(rng.choice(all_enemies))
    return picks
