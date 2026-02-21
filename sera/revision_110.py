"""Revision 1.10 combat framework primitives.

These utilities provide deterministic, testable math for element interaction,
resistance stacking, immunity/effect separation, and stall-breaking expose stacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


# ─────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────

STRONG = 0.20
ADJ = STRONG / 2
NEUTRAL = 0.0

ADJACENT_RING = ["Fire", "Air", "Water", "Ice", "Earth"]
OPPOSITES = {"Fire": "Ice", "Ice": "Fire"}


class EffectType(Enum):
    CONTROL = auto()
    AFFLICTION = auto()
    UTILITY = auto()


class DeliveryType(Enum):
    CONTACT = auto()
    PROJECTILE = auto()
    GAS = auto()
    SOUND = auto()
    LIGHT = auto()
    CURSE = auto()
    INTERNAL = auto()


@dataclass
class EffectSpec:
    tag: str
    effect_type: EffectType
    delivery_type: DeliveryType
    duration: int
    stacks: int = 1
    requires_damage: bool = False


@dataclass
class DefenseProfile:
    armor_resist: dict[str, float] = field(default_factory=dict)
    trait_resist: dict[str, float] = field(default_factory=dict)
    buff_resist: dict[str, float] = field(default_factory=dict)
    resist_multiplier: dict[str, float] = field(default_factory=dict)
    resist_cap: float = 0.90
    resist_floor: float = -1.0
    armor_element: str | None = None
    weapon_element: str | None = None
    immune_damage_types: set[str] = field(default_factory=set)
    immune_effect_types: set[EffectType] = field(default_factory=set)
    immune_effect_tags: set[str] = field(default_factory=set)
    blocked_delivery_types: set[DeliveryType] = field(default_factory=set)


@dataclass
class ExposeState:
    stacks: int = 0
    active_turns: int = 0


def element_interaction_modifier(
    attacker_weapon_element: str | None,
    defender_armor_element: str | None,
    defender_weapon_element: str | None,
    attacker_skill_element_optional: str | None = None,
) -> tuple[float, bool, str]:
    """Return (modifier, opposites_cancel_triggered, relationship)."""
    atk = attacker_skill_element_optional or attacker_weapon_element
    if not atk or not defender_armor_element:
        return NEUTRAL, False, "neutral"

    if defender_weapon_element and OPPOSITES.get(atk) == defender_weapon_element:
        return NEUTRAL, True, "opposites-cancel"

    if atk == defender_armor_element:
        return NEUTRAL, False, "neutral"

    if OPPOSITES.get(atk) == defender_armor_element:
        return STRONG, False, "strong"

    if _is_adjacent(atk, defender_armor_element):
        return ADJ, False, "adjacent"

    return NEUTRAL, False, "neutral"


def _is_adjacent(left: str, right: str) -> bool:
    if left not in ADJACENT_RING or right not in ADJACENT_RING:
        return False
    i = ADJACENT_RING.index(left)
    prev_i = (i - 1) % len(ADJACENT_RING)
    next_i = (i + 1) % len(ADJACENT_RING)
    return ADJACENT_RING[prev_i] == right or ADJACENT_RING[next_i] == right


def resolve_resistance(defense: DefenseProfile, element: str) -> tuple[float, dict[str, float | bool]]:
    base = (
        defense.armor_resist.get(element, 0.0)
        + defense.trait_resist.get(element, 0.0)
        + defense.buff_resist.get(element, 0.0)
    )

    # Ice defensive bias vs Fire: additive defensive term (not offensive).
    if defense.armor_element == "Ice" and element == "Fire":
        base += 0.05

    mult = defense.resist_multiplier.get(element, 1.0)
    scaled = base * mult
    clamped = max(defense.resist_floor, min(defense.resist_cap, scaled))

    return clamped, {
        "base_resist": base,
        "multiplier": mult,
        "scaled_resist": scaled,
        "clamped": clamped,
        "was_clamped": clamped != scaled,
    }


def apply_damage_and_effect(
    base_damage: float,
    damage_type: str,
    element: str | None,
    attacker_weapon_element: str | None,
    effect: EffectSpec | None,
    defense: DefenseProfile,
) -> dict[str, object]:
    logs: list[str] = []
    if damage_type in defense.immune_damage_types:
        final_damage = 0.0
        logs.append(f"damage blocked by immunity: {damage_type}")
    else:
        resist, resist_meta = resolve_resistance(defense, element or "") if element else (0.0, {"base_resist": 0.0, "multiplier": 1.0, "scaled_resist": 0.0, "clamped": 0.0, "was_clamped": False})
        elem_mod, cancelled, relation = element_interaction_modifier(
            attacker_weapon_element,
            defense.armor_element,
            defense.weapon_element,
        )
        raw = base_damage * (1 + elem_mod)
        final_damage = max(0.0, raw * (1 - resist))
        logs.append(f"element relation={relation} cancel={cancelled} mod={elem_mod:+.2f}")
        logs.append(f"resist base={resist_meta['base_resist']:.2f} mult={resist_meta['multiplier']:.2f} final={resist_meta['clamped']:.2f}")

    effect_result = "none"
    if effect:
        if effect.delivery_type in defense.blocked_delivery_types:
            effect_result = f"blocked delivery {effect.delivery_type.name}"
        elif effect.effect_type in defense.immune_effect_types:
            effect_result = f"blocked effect type {effect.effect_type.name}"
        elif effect.tag in defense.immune_effect_tags:
            effect_result = f"blocked effect tag {effect.tag}"
        elif effect.requires_damage and final_damage <= 0:
            effect_result = "blocked requires-damage"
        else:
            effect_result = "applied"

    return {
        "final_damage": final_damage,
        "effect_result": effect_result,
        "log": logs,
    }


def apply_expose_break(expose: ExposeState, threshold: int = 3, turns: int = 2) -> tuple[ExposeState, bool]:
    expose.stacks += 1
    if expose.stacks >= threshold:
        expose.stacks = 0
        expose.active_turns = turns
        return expose, True
    return expose, False
