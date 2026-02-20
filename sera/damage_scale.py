"""Damage scaling policy for campaign and endless modes."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class DamageScalePolicy:
    min_damage: int = 0
    hard_cap: int | None = None
    endless_wave_bonus: int = 0


DEFAULT_DAMAGE_POLICY = DamageScalePolicy()


def apply_damage_policy(damage: int, policy: DamageScalePolicy = DEFAULT_DAMAGE_POLICY, wave: int = 0) -> int:
    """Apply lower bounds, optional endless scaling, and optional hard cap."""
    scaled = damage + (policy.endless_wave_bonus * max(0, wave - 1))
    scaled = max(policy.min_damage, scaled)
    if policy.hard_cap is not None:
        scaled = min(policy.hard_cap, scaled)
    return scaled
