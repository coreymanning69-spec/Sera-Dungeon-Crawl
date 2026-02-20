"""Endless mode framework for wave progression and scaling hooks."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class EndlessProgress:
    wave: int = 1
    seed: int = 0
    total_waves_cleared: int = 0
    cumulative_kills: int = 0

    def advance_wave(self, kills_this_wave: int) -> None:
        self.total_waves_cleared += 1
        self.cumulative_kills += kills_this_wave
        self.wave += 1
