"""
Combat resolver for SERA: ENDLESS ENGAGEMENT.

Each turn:
  1. Sera's Patience ticks down (-1)
  2. Sera attacks (damage pipeline resolves)
  3. Enemy responds (annoyance resolves)
  4. Status effects tick
  5. Patience report

The math is transparent. Every number is shown.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass

from sera.weapon import Weapon
from sera.enemy import (
    Enemy,
    AnnoyanceType,
    ANNOYANCE_COST,
    ANNOYANCE_FLAVOR,
)
from sera.interest import InterestManager
from sera.status import StatusEffect


@dataclass
class CombatResult:
    """Full log of a combat encounter."""
    log: list[str]
    turns_taken: int
    enemies_killed: int
    patience_remaining: int
    game_over: bool


def resolve_combat(
    weapon: Weapon,
    enemies: list[Enemy],
    interest: InterestManager,
    max_turns: int = 20,
) -> CombatResult:
    """
    Run a full combat encounter.

    Sera attacks the first living enemy each turn.
    Enemies act in order. Simple and transparent.
    """
    log: list[str] = []
    kills = 0
    enemies = [copy.deepcopy(e) for e in enemies]  # don't mutate originals

    log.append("")
    log.append("=" * 60)
    log.append("  SERA ENTERS THE ROOM.")
    log.append(f'  Weapon: {weapon}')
    log.append(f'  Enemies: {", ".join(e.name for e in enemies)}')
    log.append("=" * 60)

    for _turn in range(max_turns):
        if interest.game_over:
            break
        if not any(e.current_hp > 0 for e in enemies):
            log.append('\n  All enemies defeated. "That was almost interesting."')
            break

        # --- Turn Start ---
        log.extend(interest.start_turn())

        # --- Sera's Attack ---
        target = next((e for e in enemies if e.current_hp > 0), None)
        if target:
            log.extend(_resolve_sera_attack(weapon, target, interest))

            # Check for kill
            if target.current_hp <= 0:
                kills += 1

        # --- Enemy Phase ---
        for enemy in enemies:
            if enemy.current_hp <= 0:
                continue
            if interest.game_over:
                break
            if enemy.is_frozen():
                log.append(f'\n  {enemy.name} is FROZEN solid! Skipping turn.')
                log.append(f'  Sera: "Stay still. I like you better this way."')
                continue
            log.extend(_resolve_enemy_turn(enemy, interest))

        # --- Status Tick ---
        for enemy in enemies:
            if enemy.current_hp > 0:
                tick_log, kill_events = enemy.tick_statuses()
                if tick_log:
                    log.extend(tick_log)
                for event in kill_events:
                    kills += 1
                    log.extend(interest.register_kill(
                        event.enemy_name,
                        event.damage_dealt,
                        event.enemy_hp_was,
                    ))
                enemy.tick_cooldowns()

        # --- Regen Phase ---
        for enemy in enemies:
            if enemy.current_hp > 0:
                healed = enemy.tick_regen()
                if healed > 0:
                    log.append(f"  {enemy.name} regenerates {healed} HP. "
                               f'({enemy.current_hp}/{enemy.max_hp}) "Annoying."')

        # --- End of Turn ---
        log.extend(interest.end_turn())

    return CombatResult(
        log=log,
        turns_taken=interest.turn_number,
        enemies_killed=kills,
        patience_remaining=interest.current_patience,
        game_over=interest.game_over,
    )


def _resolve_sera_attack(
    weapon: Weapon,
    target: Enemy,
    interest: InterestManager,
) -> list[str]:
    """Resolve Sera swinging at something."""
    log: list[str] = []

    # --- Permission Check ---
    if not target.check_permission(weapon.all_tags):
        log.append(f"\n  Sera attacks {target.name} with {weapon.display_name}...")
        log.append(f'  IMMUNE. Weapon lacks required tag. "Boring. I can\'t even touch it."')
        log.extend(interest.take_annoyance(5, f'"{target.name} is immune. What a waste of my time."'))
        return log

    # --- Damage Calculation (transparent) ---
    damage, steps = weapon.calculate_damage(target)

    log.append(f"\n  Sera attacks {target.name} with {weapon.display_name}!")
    log.append("  --- DAMAGE MATH ---")
    for step in steps:
        log.append(f"    {step}")

    # --- Apply Damage ---
    hp_before = target.current_hp
    actual, dead = target.take_damage(damage)

    if target.armor > 0 and actual < damage:
        log.append(f"  Armor absorbs {damage - actual}. ({actual} dealt)")
    else:
        log.append(f"  {actual} damage dealt!")

    log.append(f"  {target.name}: {target.current_hp}/{target.max_hp} HP")

    # --- Apply Status Effects from Affixes ---
    for affix in [weapon.prefix, weapon.suffix, weapon.set_bonus]:
        if affix and affix.inflicts_status:
            effect = StatusEffect[affix.inflicts_status]
            target.apply_status(effect, affix.status_duration, affix.status_potency)
            log.append(f'  Applied {effect.name}! "{_status_quip(effect)}"')

    # --- Kill Processing ---
    if dead:
        log.append(f'\n  {target.name} dies.')
        log.extend(interest.register_kill(target.name, damage, hp_before))

    return log


def _resolve_enemy_turn(
    enemy: Enemy,
    interest: InterestManager,
) -> list[str]:
    """Resolve one enemy's action."""
    log: list[str] = []

    ability = enemy.choose_action()

    if ability is None:
        # Enemy is charging
        if enemy.is_casting and enemy.pending_ability:
            remaining = enemy.cast_turns_remaining
            log.append(f"\n  {enemy.name} is charging {enemy.pending_ability.name}... "
                       f"({remaining} turn{'s' if remaining != 1 else ''} left)")
            log.append(f'  Sera: "Hurry up or I\'m leaving."')
        return log

    # Resolve the annoyance (WEAKENED reduces cost)
    base_cost = ANNOYANCE_COST[ability.annoyance]
    mult = enemy.get_annoyance_multiplier()
    cost = max(1, int(base_cost * mult))
    flavor = ability.flavor or ANNOYANCE_FLAVOR[ability.annoyance]

    log.append(f"\n  {enemy.name} uses {ability.name}!")
    log.append(f'  "{flavor}"')
    if mult < 1.0:
        log.append(f'  (WEAKENED: {base_cost} -> {cost} patience drain)')
    log.extend(interest.take_annoyance(cost, f"{ability.name} ({ability.annoyance.name})"))

    return log


def _status_quip(effect: StatusEffect) -> str:
    """Sera's commentary on inflicting status effects."""
    quips = {
        StatusEffect.BURNING: "Burn brighter. Entertain me.",
        StatusEffect.BLEEDING: "Bleed faster.",
        StatusEffect.SILENCED: "Finally. Quiet.",
        StatusEffect.CORRODED: "Your armor was ugly anyway.",
        StatusEffect.CURSED: "Consider this a divine opinion.",
        StatusEffect.STUNNED: "Freeze. I wasn't done with you.",
        StatusEffect.MARKED: "I see you. You can't hide.",
        StatusEffect.HUMILIATED: "That's the face of someone who knows they've lost.",
        StatusEffect.TERRIFIED: "Good instinct.",
        StatusEffect.SLOWED: "Take your time. Actually, don't.",
        StatusEffect.WEAKENED: "Feel that? That's your relevance fading.",
        StatusEffect.FROZEN: "Ice cold. Like my expectations.",
        StatusEffect.DOOMED: "Tick tock. Enjoy the countdown.",
    }
    return quips.get(effect, "Noted.")
