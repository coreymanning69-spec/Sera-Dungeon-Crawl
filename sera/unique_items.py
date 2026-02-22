"""Framework for unique weapons and one-off combat effects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UniqueItemEffect:
    key: str
    description: str


UNIQUE_ITEM_EFFECTS: dict[str, UniqueItemEffect] = {
    "Rusty Shiv Prime": UniqueItemEffect(
        key="first_blood",
        description="First hit each combat restores +1 patience.",
    ),
    "War Maul Prime": UniqueItemEffect(
        key="stagger_spike",
        description="Overkill hits restore +1 additional patience.",
    ),
}


def get_unique_effect_key(weapon_name: str) -> str | None:
    effect = UNIQUE_ITEM_EFFECTS.get(weapon_name)
    return effect.key if effect else None
