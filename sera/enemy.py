"""
Enemy system for SERA: ENDLESS ENGAGEMENT.

Enemies don't threaten Sera's life. They threaten her attention span.
Their job is to be annoying enough to drain Patience,
and interesting enough to be worth killing.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import Enum, auto

from sera.tags import DamageTag, EnemyVulnerability
from sera.status import StatusEffect, StatusInstance


class AnnoyanceType(Enum):
    """How this enemy drains Sera's Patience."""
    WEAK_HIT = auto()       # -2 PP  ("Ugh, a scratch.")
    STUN = auto()           # -10 PP ("Don't make me wait!")
    MONOLOGUE = auto()      # -50 PP after 3-turn charge ("I hate bad writing.")
    HEAL_SELF = auto()      # -5 PP  ("Stop healing. It's dragging on.")
    SUMMON = auto()         # -3 PP  ("More of you? Really?")
    DODGE_SPAM = auto()     # -4 PP  ("Stand still, insect.")


# Patience cost lookup
ANNOYANCE_COST: dict[AnnoyanceType, int] = {
    AnnoyanceType.WEAK_HIT: 2,
    AnnoyanceType.STUN: 10,
    AnnoyanceType.MONOLOGUE: 50,
    AnnoyanceType.HEAL_SELF: 5,
    AnnoyanceType.SUMMON: 3,
    AnnoyanceType.DODGE_SPAM: 3,
}

ANNOYANCE_FLAVOR: dict[AnnoyanceType, str] = {
    AnnoyanceType.WEAK_HIT: "Ugh, a scratch.",
    AnnoyanceType.STUN: "Don't. Make. Me. Wait.",
    AnnoyanceType.MONOLOGUE: "I hate bad writing.",
    AnnoyanceType.HEAL_SELF: "Stop healing. It's dragging on.",
    AnnoyanceType.SUMMON: "More of you? Really?",
    AnnoyanceType.DODGE_SPAM: "Stand still, insect.",
}


@dataclass
class EnemyAbility:
    """A specific annoyance an enemy can deploy."""
    name: str
    annoyance: AnnoyanceType
    cooldown: int = 0          # turns between uses
    charge_time: int = 0       # turns to charge (Monologue = 3)
    flavor: str = ""

    def patience_cost(self) -> int:
        return ANNOYANCE_COST[self.annoyance]


@dataclass
class Enemy:
    """
    Something unfortunate enough to be in Sera's dungeon.

    Enemies have:
    - HP (20 trash, 30 elite, 50 boss)
    - A vulnerability gate (tag requirement)
    - One or more Annoyance abilities
    - Flavor text (their last words, probably)
    """
    name: str
    max_hp: int
    archetype: str                  # "trash" | "elite" | "boss"
    vulnerability: EnemyVulnerability = EnemyVulnerability.NONE
    abilities: list[EnemyAbility] = field(default_factory=list)
    statuses: list[StatusInstance] = field(default_factory=list)
    flavor: str = ""
    regen_per_turn: int = 0         # for werewolf-type regen
    armor: int = 0                  # flat damage reduction
    dodge_chance: float = 0.0       # 0.0 - 1.0

    # --- Runtime state ---
    current_hp: int = -1            # set in __post_init__
    is_casting: bool = False
    cast_turns_remaining: int = 0
    pending_ability: EnemyAbility | None = field(default=None, repr=False)
    times_hit: int = 0
    cooldowns: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if self.current_hp == -1:
            self.current_hp = self.max_hp

    # --- Permission check ---
    def check_permission(self, weapon_tags: set[DamageTag]) -> bool:
        """Does this weapon have conceptual permission to damage this enemy?"""
        req = self.vulnerability
        if req == EnemyVulnerability.NONE:
            return True
        tag_map = {
            EnemyVulnerability.REQUIRES_DIVINE: DamageTag.DIVINE,
            EnemyVulnerability.REQUIRES_ETHEREAL: DamageTag.ETHEREAL,
            EnemyVulnerability.REQUIRES_SILVER: DamageTag.SILVER,
            EnemyVulnerability.REQUIRES_HEAVY: DamageTag.HEAVY,
            EnemyVulnerability.REQUIRES_CORROSIVE: DamageTag.CORROSIVE,
            EnemyVulnerability.REQUIRES_FIRE: DamageTag.FIRE,
            EnemyVulnerability.REQUIRES_ARCANE: DamageTag.ARCANE,
        }
        required_tag = tag_map.get(req)
        return required_tag in weapon_tags if required_tag else True

    # --- Taking damage ---
    def take_damage(self, amount: int) -> tuple[int, bool]:
        """
        Apply damage after armor.
        Returns (actual_damage_dealt, is_dead).
        """
        reduced = max(0, amount - self.armor)
        self.current_hp -= reduced
        self.times_hit += 1
        dead = self.current_hp <= 0
        return reduced, dead

    # --- Status management ---
    def apply_status(self, effect: StatusEffect, duration: int, potency: int = 1):
        # Stack: refresh duration if already present, add potency
        for s in self.statuses:
            if s.effect == effect:
                s.duration = max(s.duration, duration)
                s.potency += potency
                return
        self.statuses.append(StatusInstance(effect, duration, potency))

    def tick_statuses(self) -> list[str]:
        """Advance all status timers. Returns log of expired effects."""
        log = []
        surviving = []
        for s in self.statuses:
            if not s.tick():
                log.append(f"  {s.effect.name} expired on {self.name}.")
            else:
                surviving.append(s)
        self.statuses = surviving
        return log

    def tick_dot_damage(self) -> tuple[int, list[str]]:
        """Apply damage-over-time from status effects. Returns (total_dot, log)."""
        total = 0
        log = []
        for s in self.statuses:
            if s.effect == StatusEffect.CORRODED:
                # Armor shred — CORRODED described as armor shred, not damage
                if self.armor > 0:
                    old_armor = self.armor
                    self.armor = max(0, self.armor - s.potency)
                    shredded = old_armor - self.armor
                    if shredded > 0:
                        log.append(f"  CORRODED: -{shredded} armor from {self.name}. "
                                   f"({self.armor} armor remaining)")
                continue
            dot = s.tick_damage()
            if dot > 0:
                self.current_hp -= dot
                total += dot
                log.append(f"  {s.effect.name} deals {dot} to {self.name}. "
                           f"({self.current_hp}/{self.max_hp})")
        return total, log

    def try_dodge(self) -> bool:
        """Roll dodge chance. Returns True if the attack misses."""
        if self.dodge_chance <= 0:
            return False
        return random.random() < self.dodge_chance

    def interrupt_cast(self) -> str | None:
        """If enemy is charging, cancel it. Returns ability name or None."""
        if self.is_casting and self.pending_ability:
            name = self.pending_ability.name
            self.is_casting = False
            self.cast_turns_remaining = 0
            self.pending_ability = None
            return name
        return None

    # --- Turn AI ---
    def choose_action(self) -> EnemyAbility | None:
        """
        Simple priority AI:
        1. If stunned, skip turn entirely.
        2. If slowed, 50% chance to skip turn.
        3. If charging, continue charge.
        4. Pick first ability off cooldown, prefer high-impact.
        5. Default to weak_hit.
        """
        # STUNNED: cannot act
        if any(s.effect == StatusEffect.STUNNED for s in self.statuses):
            return None

        # SLOWED: 50% chance to skip turn
        if any(s.effect == StatusEffect.SLOWED for s in self.statuses):
            if random.random() < 0.5:
                return None

        # Continue charge
        if self.is_casting and self.pending_ability:
            self.cast_turns_remaining -= 1
            if self.cast_turns_remaining <= 0:
                self.is_casting = False
                ability = self.pending_ability
                self.pending_ability = None
                return ability
            return None  # still charging

        # Pick an ability
        for ability in sorted(self.abilities,
                              key=lambda a: ANNOYANCE_COST[a.annoyance],
                              reverse=True):
            cd = self.cooldowns.get(ability.name, 0)
            if cd > 0:
                continue
            if ability.charge_time > 0:
                # Start charging
                self.is_casting = True
                self.cast_turns_remaining = ability.charge_time
                self.pending_ability = ability
                return None  # charging started, no damage this turn
            self.cooldowns[ability.name] = ability.cooldown
            return ability

        # Fallback: basic attack
        return EnemyAbility(
            name="Flail",
            annoyance=AnnoyanceType.WEAK_HIT,
            flavor="It tries. How sad.",
        )

    def tick_cooldowns(self):
        for name in list(self.cooldowns):
            if self.cooldowns[name] > 0:
                self.cooldowns[name] -= 1

    def tick_regen(self) -> int:
        """Regenerate HP. Returns amount healed."""
        if self.regen_per_turn > 0 and self.current_hp > 0:
            healed = min(self.regen_per_turn, self.max_hp - self.current_hp)
            self.current_hp += healed
            return healed
        return 0

    def __repr__(self) -> str:
        status_str = ", ".join(str(s) for s in self.statuses)
        vuln = self.vulnerability.name if self.vulnerability != EnemyVulnerability.NONE else "OPEN"
        return (f"{self.name} [{self.archetype}] "
                f"HP:{self.current_hp}/{self.max_hp} "
                f"Armor:{self.armor} Vuln:{vuln}"
                f"{f' ({status_str})' if status_str else ''}")
