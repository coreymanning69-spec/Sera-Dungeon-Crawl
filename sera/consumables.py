"""Consumable inventory model and registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConsumableItem:
    """Single-use item that applies a simple effect."""

    key: str
    name: str
    effect: str
    potency: int
    flavor: str = ""


CONSUMABLE_REGISTRY: dict[str, ConsumableItem] = {
    "healing_flask": ConsumableItem(
        key="healing_flask",
        name="Healing Flask",
        effect="restore_patience",
        potency=12,
        flavor='"Better. Keep the momentum."',
    ),
    "focus_tonic": ConsumableItem(
        key="focus_tonic",
        name="Focus Tonic",
        effect="restore_patience",
        potency=8,
        flavor='"Fine. This will do."',
    ),
}


def get_consumable(key: str) -> ConsumableItem | None:
    return CONSUMABLE_REGISTRY.get(key)
