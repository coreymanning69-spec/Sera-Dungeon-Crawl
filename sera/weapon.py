"""
Weapon system for SERA: ENDLESS ENGAGEMENT.

Weapons are small-number engines. A base of 1-3 becomes 25
through Prefixes, Suffixes, Set Bonuses, and Tag interactions.
You're building a logic bomb, not finding a bigger stick.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sera.tags import DamageTag
from sera.status import StatusEffect

if TYPE_CHECKING:
    from sera.enemy import Enemy


# ---------------------------------------------------------------------------
# Affixes: the modular brain of every weapon
# ---------------------------------------------------------------------------

@dataclass
class Affix:
    """A prefix or suffix that bolts conditional math onto a weapon."""
    name: str
    description: str               # Sera-voice flavor
    affix_type: str                # "prefix" | "suffix"

    # --- flat bonuses (added BEFORE multipliers) ---
    flat_bonus: int = 0
    flat_condition: str = "always"  # condition key (see combat resolver)

    # --- multipliers (applied AFTER flat bonuses) ---
    multiplier: float = 1.0
    mult_condition: str = "always"

    # --- per-stack bonuses ---
    per_stack_bonus: int = 0
    per_stack_source: str = ""     # e.g. "debuffs_on_target"

    # --- tag granted ---
    granted_tag: DamageTag | None = None

    # --- status inflicted on hit ---
    inflicts_status: str | None = None
    status_duration: int = 0
    status_potency: int = 1

    def describe(self) -> str:
        return f'[{self.affix_type.upper()}] {self.name}: "{self.description}"'


# ---------------------------------------------------------------------------
# Weapon: the core object
# ---------------------------------------------------------------------------

@dataclass
class Weapon:
    """
    A weapon Sera deigns to hold.

    Math pipeline per hit:
        1. Start with base_damage
        2. Add flat bonuses from affixes (if conditions met)
        3. Multiply by multipliers from affixes (if conditions met)
        4. Add per-stack bonuses (e.g. +1 per debuff on target)
        5. Clamp to [0, 30] (we said small numbers, we meant it)
    """
    name: str
    base_damage: int               # 1-3 range
    tags: list[DamageTag] = field(default_factory=list)
    prefix: Affix | None = None
    suffix: Affix | None = None
    set_bonus: Affix | None = None
    flavor: str = ""               # Sera's opinion of this weapon

    @property
    def display_name(self) -> str:
        parts = []
        if self.prefix:
            parts.append(self.prefix.name)
        parts.append(self.name)
        if self.suffix:
            parts.append(self.suffix.name)
        return " ".join(parts)

    @property
    def all_tags(self) -> set[DamageTag]:
        """Collect tags from base weapon + any affix-granted tags."""
        tags = set(self.tags)
        for affix in [self.prefix, self.suffix, self.set_bonus]:
            if affix and affix.granted_tag:
                tags.add(affix.granted_tag)
        return tags

    def calculate_damage(self, enemy: Enemy, enemy_count: int = 1) -> tuple[int, list[str]]:
        """
        Resolve the full damage pipeline against a target.
        Returns (final_damage, list_of_math_steps_for_display).

        enemy_count: number of living enemies in the encounter (used for enemy_alone condition).
        """
        steps: list[str] = []
        dmg = self.base_damage
        steps.append(f"Base: {dmg}")

        # --- Phase 1: Flat bonuses ---
        for affix in [self.prefix, self.suffix, self.set_bonus]:
            if affix and affix.flat_bonus != 0:
                if _check_condition(affix.flat_condition, enemy, enemy_count):
                    dmg += affix.flat_bonus
                    steps.append(f'  + {affix.flat_bonus} ({affix.name}: {affix.flat_condition}) = {dmg}')

        # --- Phase 2: Multipliers ---
        for affix in [self.prefix, self.suffix, self.set_bonus]:
            if affix and affix.multiplier != 1.0:
                if _check_condition(affix.mult_condition, enemy, enemy_count):
                    dmg = int(dmg * affix.multiplier)
                    steps.append(f'  x {affix.multiplier} ({affix.name}: {affix.mult_condition}) = {dmg}')

        # --- Phase 3: Per-stack bonuses ---
        for affix in [self.prefix, self.suffix, self.set_bonus]:
            if affix and affix.per_stack_bonus != 0 and affix.per_stack_source:
                stacks = _count_stacks(affix.per_stack_source, enemy)
                bonus = affix.per_stack_bonus * stacks
                if bonus > 0:
                    dmg += bonus
                    steps.append(f'  + {affix.per_stack_bonus} x {stacks} stacks ({affix.name}) = {dmg}')

        # --- Clamp ---
        dmg = max(0, min(30, dmg))
        steps.append(f"Final (clamped 0-30): {dmg}")
        return dmg, steps

    def add_tag(self, tag: DamageTag) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def __repr__(self) -> str:
        tag_str = ", ".join(t.name for t in self.all_tags)
        return f"{self.display_name} ({self.base_damage} dmg) [{tag_str}]"


# ---------------------------------------------------------------------------
# Condition resolver — keeps affix logic declarative
# ---------------------------------------------------------------------------

def _check_condition(condition: str, enemy: Enemy, enemy_count: int = 1) -> bool:
    """Evaluate a named condition against the current enemy state."""
    if condition == "always":
        return True
    if condition == "enemy_full_hp":
        return enemy.current_hp >= enemy.max_hp
    if condition == "enemy_below_half":
        return enemy.current_hp < enemy.max_hp // 2
    if condition == "enemy_casting":
        return enemy.is_casting
    if condition == "enemy_has_debuffs":
        return len(enemy.statuses) > 0
    if condition == "enemy_alone":
        return enemy_count <= 1
    if condition == "first_hit":
        return enemy.times_hit == 0
    if condition == "enemy_marked":
        return any(s.effect == StatusEffect.MARKED for s in enemy.statuses)
    return False


def _count_stacks(source: str, enemy: Enemy) -> int:
    """Count stacks for per-stack bonuses."""
    if source == "debuffs_on_target":
        return len(enemy.statuses)
    if source == "missing_hp_percent":
        missing = enemy.max_hp - enemy.current_hp
        return (missing * 10) // enemy.max_hp  # 0-10 scale
    return 0
