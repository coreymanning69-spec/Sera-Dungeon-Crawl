"""Framework for unique weapons and one-off combat effects."""

from __future__ import annotations

from dataclasses import dataclass, field

from sera.weapon import Affix


@dataclass(frozen=True)
class UniqueItemEffect:
    key: str
    description: str


@dataclass(frozen=True)
class UniqueItemProfile:
    name: str
    item_type: str = "Weapon"
    max_level: int = 20
    modifiers: tuple[Affix, ...] = field(default_factory=tuple)
    effects: tuple[UniqueItemEffect, ...] = field(default_factory=tuple)

    def scaled_modifiers(self) -> tuple[Affix, ...]:
        """Respect the 5-slot modifier cap when exposing profile modifiers."""
        return self.modifiers[:5]


UNIQUE_ITEM_PROFILES: dict[str, UniqueItemProfile] = {
    "Rusty Shiv Prime": UniqueItemProfile(
        name="Rusty Shiv Prime",
        item_type="Dagger",
        max_level=20,
        modifiers=(
            Affix(name="first_blood", description="First hit each combat restores +1 patience.", affix_type="unique"),
            Affix(name="turn_surge", description="10% chance to gain an immediate extra turn after a kill.", affix_type="unique"),
        ),
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
        item_type="Maul",
        max_level=20,
        modifiers=(
            Affix(name="stagger_spike", description="Overkill hits restore +1 additional patience.", affix_type="unique"),
            Affix(name="damage_bloom", description="Every third hit multiplies total damage by 1.25.", affix_type="unique"),
        ),
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
        item_type="Rapier",
        max_level=20,
        modifiers=(
            Affix(name="immunity_void", description="Ignores one immunity check per combat.", affix_type="unique"),
            Affix(name="duelist_stride", description="After dodging, next hit gets +2 flat damage.", affix_type="unique"),
        ),
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
    "Hazirawn": UniqueItemProfile(
        name="Hazirawn",
        item_type="Greatsword",
        max_level=20,
        modifiers=(
            Affix(name="first_blood", description="Guaranteed crit on targets at full HP.", affix_type="unique"),
            Affix(name="necrotic_decay", description="Applies a scaling necrotic damage-over-time effect.", affix_type="unique"),
            Affix(name="anti_heal", description="Prevents enemy healing for 1 turn.", affix_type="unique"),
        ),
    ),
    "Black Dragon Mask": UniqueItemProfile(
        name="Black Dragon Mask",
        item_type="Wondrous",
        max_level=20,
        modifiers=(
            Affix(name="acid_immunity", description="Nullifies acid damage.", affix_type="unique"),
            Affix(name="legendary_resistance", description="Auto-pass one failed save per wave.", affix_type="unique"),
        ),
    ),
    "Insignia of Claws": UniqueItemProfile(
        name="Insignia of Claws",
        item_type="Trinket",
        max_level=10,
        modifiers=(
            Affix(name="empowered_strikes", description="Unarmed strikes gain magical bonus damage.", affix_type="unique"),
        ),
    ),
}


ARTIFACT_EFFECT_ROTATION: tuple[tuple[str, str], ...] = (
    ("first_blood", "First hit each combat restores +1 patience."),
    ("turn_surge", "10% chance to gain an immediate extra turn after a kill."),
    ("stagger_spike", "Overkill hits restore +1 additional patience."),
    ("damage_bloom", "Every third hit multiplies total damage by 1.25."),
    ("duelist_stride", "After dodging, next hit gets +2 flat damage."),
)


ARTIFACT_NAMES: tuple[str, ...] = (
    "Asterion, Star-Eater Blade",
    "Vesper Bell of Last Rites",
    "Crownsplitter Relic-Axe",
    "Morrowglass Needle",
    "Choir of Cinders",
    "Thorn of the First Oath",
    "Nullwake Prism",
    "Wintercourt Verdict",
    "Gloamchain Testament",
    "Pilgrim's Ember Canon",
    "Sable Tide Harpoon",
    "Ruin Psalm Censer",
    "Iron Vow Breaker",
    "Catacomb Lantern IX",
    "The Quiet Catastrophe",
    "Saintfall Meteor Hammer",
    "Abyssal Court Sabre",
    "Howling Reliquary Pike",
    "Ivory Eclipse Fang",
    "Godshard Cauterizer",
)


for idx, artifact_name in enumerate(ARTIFACT_NAMES):
    if artifact_name in UNIQUE_ITEM_PROFILES:
        continue
    effect_a = ARTIFACT_EFFECT_ROTATION[idx % len(ARTIFACT_EFFECT_ROTATION)]
    effect_b = ARTIFACT_EFFECT_ROTATION[(idx + 2) % len(ARTIFACT_EFFECT_ROTATION)]
    UNIQUE_ITEM_PROFILES[artifact_name] = UniqueItemProfile(
        name=artifact_name,
        item_type="Artifact",
        max_level=20,
        modifiers=(
            Affix(name=effect_a[0], description=effect_a[1], affix_type="unique"),
            Affix(name=effect_b[0], description=effect_b[1], affix_type="unique"),
        ),
        effects=(
            UniqueItemEffect(key=effect_a[0], description=effect_a[1]),
            UniqueItemEffect(key=effect_b[0], description=effect_b[1]),
        ),
    )


def get_unique_effects(weapon_name: str) -> tuple[UniqueItemEffect, ...]:
    profile = UNIQUE_ITEM_PROFILES.get(weapon_name)
    if not profile:
        return tuple()
    if profile.effects:
        return profile.effects
    return tuple(
        UniqueItemEffect(key=mod.name, description=mod.description)
        for mod in profile.scaled_modifiers()
    )


def get_unique_effect_key(weapon_name: str) -> str | None:
    effects = get_unique_effects(weapon_name)
    return effects[0].key if effects else None


def is_unique_weapon_name(weapon_name: str) -> bool:
    return weapon_name in UNIQUE_ITEM_PROFILES
