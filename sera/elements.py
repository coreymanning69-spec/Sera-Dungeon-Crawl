"""Element interaction framework used by combat and defense pipelines."""

from __future__ import annotations

from sera.tags import DamageTag

ELEMENTS: list[DamageTag] = [
    DamageTag.FIRE,
    DamageTag.AIR,
    DamageTag.WATER,
    DamageTag.ICE,
    DamageTag.EARTH,
    DamageTag.DIVINE,
]

OPPOSITES: dict[DamageTag, DamageTag] = {
    DamageTag.FIRE: DamageTag.ICE,
    DamageTag.ICE: DamageTag.FIRE,
}

ADJACENT_RING: list[DamageTag] = [
    DamageTag.FIRE,
    DamageTag.AIR,
    DamageTag.WATER,
    DamageTag.ICE,
    DamageTag.EARTH,
]

ADJACENT_HALF_MAGNITUDE = True
OPPOSITES_CANCEL_IF_BOTH_WIELDED = True

ICE_DEFENSIVE_BIAS_VS_FIRE = 0.20
WATER_DEFENSIVE_BIAS_VS_FIRE = 0.10


def opposite_of(tag: DamageTag) -> DamageTag | None:
    return OPPOSITES.get(tag)


def is_adjacent(a: DamageTag, b: DamageTag) -> bool:
    if a not in ADJACENT_RING or b not in ADJACENT_RING:
        return False
    ai = ADJACENT_RING.index(a)
    left = ADJACENT_RING[(ai - 1) % len(ADJACENT_RING)]
    right = ADJACENT_RING[(ai + 1) % len(ADJACENT_RING)]
    return b in (left, right)


def resistance_modifier(attacker: DamageTag, defender: DamageTag) -> float:
    """Return defensive resistance contribution for one attacker/defender element pair."""
    if attacker == DamageTag.FIRE and defender == DamageTag.ICE:
        return ICE_DEFENSIVE_BIAS_VS_FIRE

    if attacker == DamageTag.FIRE and defender == DamageTag.WATER:
        return WATER_DEFENSIVE_BIAS_VS_FIRE

    if OPPOSITES_CANCEL_IF_BOTH_WIELDED and opposite_of(attacker) == defender:
        return 0.0

    if attacker == defender:
        return 0.10

    if ADJACENT_HALF_MAGNITUDE and is_adjacent(attacker, defender):
        return 0.05

    return 0.0
