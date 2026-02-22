"""Framework for unique weapons and one-off combat effects."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UniqueItemEffect:
    key: str
    description: str


@dataclass(frozen=True)
class UniqueItemProfile:
    name: str
    effects: tuple[UniqueItemEffect, ...] = field(default_factory=tuple)


UNIQUE_ITEM_PROFILES: dict[str, UniqueItemProfile] = {
    "Rusty Shiv Prime": UniqueItemProfile(
        name="Rusty Shiv Prime",
        effects=(
            UniqueItemEffect(
                key="first_blood",
                description="First hit each combat restores +1 patience.",
            ),
            UniqueItemEffect(
                key="turn_surge",
                description="10% chance to gain an immediate extra turn after a kill.",
            ),
        ),
    ),
    "War Maul Prime": UniqueItemProfile(
        name="War Maul Prime",
        effects=(
            UniqueItemEffect(
                key="stagger_spike",
                description="Overkill hits restore +1 additional patience.",
            ),
            UniqueItemEffect(
                key="damage_bloom",
                description="Every third hit multiplies total damage by 1.25.",
            ),
        ),
    ),
    "Moonthread Needle Prime": UniqueItemProfile(
        name="Moonthread Needle Prime",
        effects=(
            UniqueItemEffect(
                key="immunity_void",
                description="Ignores one immunity check per combat.",
            ),
            UniqueItemEffect(
                key="duelist_stride",
                description="After dodging, next hit gets +2 flat damage.",
            ),
        ),
    ),
}


def get_unique_effects(weapon_name: str) -> tuple[UniqueItemEffect, ...]:
    profile = UNIQUE_ITEM_PROFILES.get(weapon_name)
    return profile.effects if profile else tuple()


def get_unique_effect_key(weapon_name: str) -> str | None:
    effects = get_unique_effects(weapon_name)
    return effects[0].key if effects else None


def is_unique_weapon_name(weapon_name: str) -> bool:
    return weapon_name in UNIQUE_ITEM_PROFILES
