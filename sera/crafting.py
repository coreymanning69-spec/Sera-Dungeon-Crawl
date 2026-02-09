"""
Crafting system — the Upgrade Loop.

You don't buy stats. You modify the concept of the weapon.
An Iron Sword becomes a Moon-Touched Claymore.
Tags change. Permission expands. Sera gets new toys.
"""

from __future__ import annotations
from dataclasses import dataclass

from sera.tags import DamageTag
from sera.weapon import Weapon, Affix


@dataclass
class CraftingMaterial:
    """A material that modifies a weapon's identity."""
    name: str
    grants_tag: DamageTag | None = None
    grants_prefix: Affix | None = None
    grants_suffix: Affix | None = None
    rename_to: str | None = None       # optional: change weapon base name
    flavor: str = ""


# Pre-built crafting materials
CRAFTING_MATERIALS = {
    "Moonstone": CraftingMaterial(
        name="Moonstone",
        grants_tag=DamageTag.DIVINE,
        flavor='"Touched by moonlight. Now it kills things that think they\'re already dead."',
    ),
    "Vial of Ectoplasm": CraftingMaterial(
        name="Vial of Ectoplasm",
        grants_tag=DamageTag.ETHEREAL,
        flavor='"Ghosts hate this one weird trick."',
    ),
    "Silver Dust": CraftingMaterial(
        name="Silver Dust",
        grants_tag=DamageTag.SILVER,
        flavor='"For when the full moon brings out the tedious."',
    ),
    "Whetstone of Ruin": CraftingMaterial(
        name="Whetstone of Ruin",
        grants_tag=DamageTag.HEAVY,
        flavor='"Makes it heavier. Makes it meaner. Makes it mine."',
    ),
    "Acidic Resin": CraftingMaterial(
        name="Acidic Resin",
        grants_tag=DamageTag.CORROSIVE,
        flavor='"Dissolves armor. Dissolves pride. Same thing."',
    ),
    "Ember Core": CraftingMaterial(
        name="Ember Core",
        grants_tag=DamageTag.FIRE,
        flavor='"Everything is better on fire."',
    ),
    "Arcane Lens": CraftingMaterial(
        name="Arcane Lens",
        grants_tag=DamageTag.ARCANE,
        flavor='"Now it hits things that think they\'re smart."',
    ),
}


def apply_material(weapon: Weapon, material: CraftingMaterial) -> list[str]:
    """
    Apply a crafting material to a weapon.
    Returns a log of what changed.
    """
    log = []
    old_name = weapon.display_name

    if material.grants_tag:
        weapon.add_tag(material.grants_tag)
        log.append(f"  Added [{material.grants_tag.name}] tag.")

    if material.grants_prefix:
        weapon.prefix = material.grants_prefix
        log.append(f"  Applied prefix: {material.grants_prefix.name}")

    if material.grants_suffix:
        weapon.suffix = material.grants_suffix
        log.append(f"  Applied suffix: {material.grants_suffix.name}")

    if material.rename_to:
        weapon.name = material.rename_to

    log.insert(0, f"\n  CRAFT: {old_name} + {material.name} = {weapon.display_name}")
    log.append(f"  Tags: [{', '.join(t.name for t in weapon.all_tags)}]")
    if material.flavor:
        log.append(f"  Sera: {material.flavor}")

    return log
