"""
Status effects (debuffs/buffs) for the Drama Queen engine.

Every debuff on a target is another reason Sera is entertained.
"""

from enum import Enum, auto


class StatusEffect(Enum):
    BURNING = auto()
    BLEEDING = auto()
    SILENCED = auto()
    CORRODED = auto()
    CURSED = auto()
    STUNNED = auto()
    SLOWED = auto()
    MARKED = auto()       # "I see you."
    HUMILIATED = auto()   # "You're pathetic."
    TERRIFIED = auto()    # "Good. Fear me."
    WEAKENED = auto()     # Reduces patience drain from enemy actions
    FROZEN = auto()       # Skips enemy turn entirely
    DOOMED = auto()       # Detonates for big damage when duration expires


class StatusInstance:
    """A single active status effect on a combatant."""

    def __init__(self, effect: StatusEffect, duration: int, potency: int = 1):
        self.effect = effect
        self.duration = duration    # turns remaining
        self.potency = potency      # stacking intensity

    def tick(self) -> bool:
        """Advance one turn. Returns False when expired."""
        self.duration -= 1
        return self.duration > 0

    def tick_damage(self) -> int:
        """Return damage-over-time for this tick. Potency scales it."""
        if self.effect == StatusEffect.BURNING:
            return self.potency      # 1 per potency stack
        if self.effect == StatusEffect.BLEEDING:
            return self.potency      # 1 per potency stack
        if self.effect == StatusEffect.CORRODED:
            return 0                 # armor shred, not damage
        return 0

    def detonate_damage(self) -> int:
        """Return burst damage when DOOMED expires. 0 for other effects."""
        if self.effect == StatusEffect.DOOMED:
            return self.potency * 5  # 5 damage per potency stack
        return 0

    def annoyance_reduction(self) -> float:
        """Return patience-drain multiplier. 1.0 = normal, <1.0 = reduced."""
        if self.effect == StatusEffect.WEAKENED:
            return max(0.2, 1.0 - 0.25 * self.potency)  # 25% less per stack, floor 20%
        return 1.0

    def prevents_action(self) -> bool:
        """Whether this status prevents the enemy from acting."""
        return self.effect == StatusEffect.FROZEN

    def __repr__(self) -> str:
        return f"{self.effect.name}({self.duration}t)"
