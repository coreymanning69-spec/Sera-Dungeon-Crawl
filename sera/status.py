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

    def __repr__(self) -> str:
        return f"{self.effect.name}({self.duration}t)"
