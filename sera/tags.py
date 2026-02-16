"""
Tag system for the Permission mechanic.

Damage isn't physics. It's Concept.
If the weapon can't conceptually threaten the enemy, it deals nothing.
"""

from enum import Enum, auto


class DamageTag(Enum):
    """Tags that define what a weapon IS, conceptually."""
    PHYSICAL = auto()
    HEAVY = auto()
    DIVINE = auto()
    ETHEREAL = auto()
    SILVER = auto()
    CORROSIVE = auto()
    FIRE = auto()
    ICE = auto()
    ARCANE = auto()
    BLEED = auto()
    SONIC = auto()


class EnemyVulnerability(Enum):
    """What makes an enemy stop being Boring."""
    REQUIRES_DIVINE = auto()      # Ghosts, spirits
    REQUIRES_ETHEREAL = auto()    # Ghosts, spirits (alternative)
    REQUIRES_SILVER = auto()      # Werewolves, shapeshifters
    REQUIRES_HEAVY = auto()       # Armored enemies
    REQUIRES_CORROSIVE = auto()   # Armored enemies (alternative)
    REQUIRES_FIRE = auto()        # Trolls, regenerators
    REQUIRES_ARCANE = auto()      # Magic-resistant constructs
    NONE = auto()                 # Anything works. Basic trash.
