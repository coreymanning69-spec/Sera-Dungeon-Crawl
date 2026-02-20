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

import random

from sera.weapon import Weapon
from sera.enemy import Enemy, AnnoyanceType, ANNOYANCE_COST, ANNOYANCE_FLAVOR
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
    final_enemies: list[Enemy]  # deepcopied enemies with final HP/status state


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
        living_count = sum(1 for e in enemies if e.current_hp > 0)
        if target:
            log.extend(_resolve_sera_attack(weapon, target, interest, living_count))

            # Check for kill
            if target.current_hp <= 0:
                kills += 1

        # --- Enemy Phase ---
        for enemy in enemies:
            if enemy.current_hp <= 0:
                continue
            if interest.game_over:
                break
            log.extend(_resolve_enemy_turn(enemy, interest))

        # --- Status Tick (DoT damage first, then expire durations) ---
        for enemy in enemies:
            if enemy.current_hp > 0:
                dot_total, dot_log = enemy.tick_dot_damage()
                if dot_log:
                    log.extend(dot_log)
                if dot_total > 0 and enemy.current_hp <= 0:
                    kills += 1
                    log.append(f'\n  {enemy.name} succumbs to the damage over time.')
                    log.extend(interest.register_kill(enemy.name, dot_total, dot_total))
                tick_log = enemy.tick_statuses()
                if tick_log:
                    log.extend(tick_log)
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
        final_enemies=enemies,
    )


def _resolve_sera_attack(
    weapon: Weapon,
    target: Enemy,
    interest: InterestManager,
    living_count: int = 1,
) -> list[str]:
    """Resolve Sera swinging at something."""
    log: list[str] = []

    # --- Permission Check ---
    if not target.check_permission(weapon.all_tags):
        immune_quip = random.choice([
            "Boring. I can't even touch it.",
            "I can't touch it. YOUR fault.",
            "The wrong weapon. Again. Think.",
        ])
        log.append(f"\n  Sera attacks {target.name} with {weapon.display_name}...")
        log.append(f'  IMMUNE. Weapon lacks required tag. "{immune_quip}"')
        log.extend(interest.take_annoyance(5, f'"{target.name} is immune. What a waste of my time."'))
        return log

    # --- Damage Calculation (transparent) ---
    damage, steps = weapon.calculate_damage(target, enemy_count=living_count)

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
            wait_quip = random.choice([
                "Hurry up or I'm leaving.",
                "Three turns? I don't have three turns.",
                "Charging something. Cute. Hurry.",
            ])
            log.append(f"\n  {enemy.name} is charging {enemy.pending_ability.name}... "
                       f"({remaining} turn{'s' if remaining != 1 else ''} left)")
            log.append(f'  Sera: "{wait_quip}"')
        return log

    # Resolve the annoyance
    cost = ANNOYANCE_COST[ability.annoyance]
    flavor = ability.flavor or ANNOYANCE_FLAVOR[ability.annoyance]

    log.append(f"\n  {enemy.name} uses {ability.name}!")
    log.append(f'  "{flavor}"')
    log.extend(interest.take_annoyance(cost, f"{ability.name} ({ability.annoyance.name})"))

    # HEAL_SELF abilities actually heal the enemy
    if ability.annoyance == AnnoyanceType.HEAL_SELF:
        heal_amount = min(5, enemy.max_hp - enemy.current_hp)
        if heal_amount > 0:
            enemy.current_hp += heal_amount
            log.append(f"  {enemy.name} heals {heal_amount} HP. "
                       f"({enemy.current_hp}/{enemy.max_hp})")
            log.append('  Sera: "Stop healing. It\'s dragging on."')

    return log


def _status_quip(effect: StatusEffect) -> str:
    """Sera's commentary on inflicting status effects."""
    quips: dict[StatusEffect, list[str]] = {
        StatusEffect.BURNING: ["Burn brighter. Entertain me.", "There we go. Brighter."],
        StatusEffect.BLEEDING: ["Bleed faster.", "Keep bleeding. Faster."],
        StatusEffect.SILENCED: ["Finally. Quiet.", "Better. Much better."],
        StatusEffect.CORRODED: ["Your armor was ugly anyway.", "Armor was decorative anyway."],
        StatusEffect.CURSED: ["Consider this a divine opinion.", "A divine annotation."],
        StatusEffect.STUNNED: ["Freeze. I wasn't done with you."],
        StatusEffect.MARKED: ["I see you. You can't hide."],
        StatusEffect.HUMILIATED: ["That's the face of someone who knows they've lost."],
        StatusEffect.TERRIFIED: ["Good instinct."],
        StatusEffect.SLOWED: ["Take your time. Actually, don't."],
    }
    options = quips.get(effect, ["Noted."])
    return random.choice(options)
