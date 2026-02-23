"""Named NPC encounter framework for traders and enchanters."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NPCOffer:
    key: str
    label: str
    cost_gold: int
    description: str


@dataclass(frozen=True)
class NamedNPC:
    name: str
    role: str  # trader | enchanter
    intro: str
    offers: list[NPCOffer] = field(default_factory=list)


TRADER_OFFERS = [
    NPCOffer("buy_shards", "Buy 3 Upgrade Shards", 15, "Small steel vials of crystal dust."),
    NPCOffer("buy_flask", "Buy Healing Flask", 20, "A stop-gap for when things drag."),
    NPCOffer("buy_random_equipment", "Buy random equipment", 35, "Unidentified but serviceable gear."),
]

ENCHANTER_OFFERS = [
    NPCOffer("enchant_weapon", "Enchant equipped weapon (+1 upgrade level)", 40, "Unsafe, expensive, effective."),
    NPCOffer("infuse_armor", "Infuse one stash armor (+1 random stat)", 30, "Threaded with spite and silver."),
]

NPC_POOL = [
    NamedNPC("Veyra the Quartermaster", "trader", "I price it. You carry it.", TRADER_OFFERS),
    NamedNPC("Drald Ironhand", "trader", "Coins first. Complaints later.", TRADER_OFFERS),
    NamedNPC("Sister Nox", "enchanter", "I can make it hurt more. Pay me.", ENCHANTER_OFFERS),
    NamedNPC("Caldris Rune-Dealer", "enchanter", "Runes are honest. People are not.", ENCHANTER_OFFERS),
]


def roll_npc_for_floor(floor: int, rand) -> NamedNPC | None:
    """Simple framework: chance for one named NPC to appear between floors."""
    chance = min(0.2 + floor * 0.06, 0.65)
    if rand.random() > chance:
        return None
    return rand.choice(NPC_POOL)
