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
import random
from dataclasses import dataclass

import random

from sera.weapon import Weapon
from sera.enemy import (
    Enemy,
    AnnoyanceType,
    ANNOYANCE_COST,
    ANNOYANCE_FLAVOR,
)
from sera.interest import InterestManager
from sera.status import StatusEffect
from sera.tags import DamageTag


BASE_STAT_DAMAGE = 1
MISS_PATIENCE_SCALE = 0.20
DODGE_PATIENCE_COST = 2
MISS_PATIENCE_COST = 1
WRONG_ELEMENT_PATIENCE_COST = 1


@dataclass
class CombatDamageBonuses:
    """External additive bonuses for the 7-step damage pipeline."""
    amulet_cloak: int = 0
    gloves_boots: int = 0
    other_equipment: int = 0


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
    damage_bonuses: CombatDamageBonuses | None = None,
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
            log.extend(_resolve_sera_attack(
                weapon,
                target,
                interest,
                damage_bonuses or CombatDamageBonuses(),
            ))

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

        # --- Status Tick (DoT damage first, then expire durations) ---
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
        final_enemies=enemies,
    )


def _resolve_sera_attack(
    weapon: Weapon,
    target: Enemy,
    interest: InterestManager,
    damage_bonuses: CombatDamageBonuses,
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

    # Low-patience miss chance
    patience_ratio = interest.current_patience / interest.max_patience
    miss_chance = max(0.0, (1.0 - patience_ratio) * MISS_PATIENCE_SCALE)
    if random.random() < miss_chance:
        log.append(f"\n  Sera attacks {target.name} with {weapon.display_name}...")
        log.append('  MISS. "I am losing interest."')
        log.extend(interest.take_annoyance(MISS_PATIENCE_COST, 'A lazy swing misses.'))
        return log

    # --- 7-step Damage Calculation (transparent) ---
    damage, steps, had_wrong_element = _calculate_pipeline_damage(
        weapon=weapon,
        target=target,
        damage_bonuses=damage_bonuses,
    )

    # --- Defense Phase: Armor -> Dodge -> Elemental Resistance ---
    final_damage, defense_steps, dodged = _apply_enemy_defenses(weapon, target, damage)


    log.append(f"\n  Sera attacks {target.name} with {weapon.display_name}!")

    # --- Interrupt Check (hitting a charging enemy cancels the charge) ---
    interrupted = target.interrupt_cast()
    if interrupted:
        log.append(f'  {target.name}\'s {interrupted} was INTERRUPTED!')
        log.append('  Sera: "I said shut up." [+3 Patience]')
        interest._restore(3)

    log.append("  --- DAMAGE MATH ---")
    for step in steps:
        log.append(f"    {step}")
    for step in defense_steps:
        log.append(f"    {step}")

    if dodged:
        log.append(f"  {target.name} dodges. Nothing lands.")
        log.extend(interest.take_annoyance(DODGE_PATIENCE_COST, f"{target.name} dodged."))
        return log

    if had_wrong_element:
        log.extend(interest.take_annoyance(WRONG_ELEMENT_PATIENCE_COST, "Wrong element. Mediocre."))

    # --- Apply Damage ---
    hp_before = target.current_hp
    target.current_hp -= final_damage
    target.times_hit += 1
    dead = target.current_hp <= 0

    log.append(f"  {final_damage} damage dealt!")

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
        log.extend(interest.register_kill(target.name, final_damage, hp_before))

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


def _calculate_pipeline_damage(
    weapon: Weapon,
    target: Enemy,
    damage_bonuses: CombatDamageBonuses,
) -> tuple[int, list[str], bool]:
    """Resolve 7 additive steps, with elemental as the only multiplier."""
    steps: list[str] = []
    damage = 0

    # 1) Base stat contribution (~1)
    damage += BASE_STAT_DAMAGE
    steps.append(f"1) Base stat contribution: +{BASE_STAT_DAMAGE} = {damage}")

    # 2) Weapon base damage
    weapon_base = weapon.effective_base_damage
    damage += weapon_base
    steps.append(f"2) Weapon base ({weapon.name}): +{weapon_base} = {damage}")

    # 3) Amulet + Cloak enchants
    damage += damage_bonuses.amulet_cloak
    steps.append(f"3) Amulet/Cloak enchants: +{damage_bonuses.amulet_cloak} = {damage}")

    # 4) Gloves + Boots enchants
    damage += damage_bonuses.gloves_boots
    steps.append(f"4) Gloves/Boots enchants: +{damage_bonuses.gloves_boots} = {damage}")

    # 5) Other equipment enchants
    damage += damage_bonuses.other_equipment
    steps.append(f"5) Other equipment enchants: +{damage_bonuses.other_equipment} = {damage}")

    # 6) Elemental bonus (only multiplicative layer)
    mult = _elemental_multiplier(weapon.all_tags, target)
    damage = int(damage * mult)
    steps.append(f"6) Elemental modifier: x{mult:.1f} = {damage}")

    # 7) Other flat bonuses (weapon affixes + target debuff pressure)
    other_bonus, other_notes = _other_flat_bonus(weapon, target)
    damage += other_bonus
    steps.append(f"7) Other bonuses: +{other_bonus} = {damage}")
    for note in other_notes:
        steps.append(f"   - {note}")

    clamped = max(0, min(30, damage))
    if clamped != damage:
        steps.append(f"Clamp (0-30): {damage} -> {clamped}")
    else:
        steps.append(f"Clamp (0-30): {clamped}")

    wrong_element = _used_resisted_element_without_weakness(weapon.all_tags, target)
    return clamped, steps, wrong_element


def _elemental_multiplier(weapon_tags: set[DamageTag], target: Enemy) -> float:
    """Element matchup multiplier for step 6."""
    if DamageTag.ETHEREAL in weapon_tags:
        return 1.0
    if any(tag in target.elemental_weaknesses for tag in weapon_tags):
        return 2.0
    return 1.0


def _used_resisted_element_without_weakness(weapon_tags: set[DamageTag], target: Enemy) -> bool:
    """Wrong-element detector for PP penalty."""
    if DamageTag.ETHEREAL in weapon_tags:
        return False
    has_resisted = any(tag in target.elemental_resistances for tag in weapon_tags)
    has_weakness = any(tag in target.elemental_weaknesses for tag in weapon_tags)
    return has_resisted and not has_weakness


def _other_flat_bonus(weapon: Weapon, target: Enemy) -> tuple[int, list[str]]:
    """Flatten affix effects into the additive step-7 bucket."""
    bonus = 0
    notes: list[str] = []

    # Left-to-right affix priority on display name: prefix -> base -> suffix.
    for affix in [weapon.prefix, weapon.suffix, weapon.set_bonus]:
        if not affix:
            continue
        if affix.flat_bonus and _check_condition(affix.flat_condition, target):
            bonus += affix.flat_bonus
            notes.append(f"{affix.name}: +{affix.flat_bonus}")
        if affix.per_stack_bonus and affix.per_stack_source:
            stacks = _count_stacks(affix.per_stack_source, target)
            stack_bonus = affix.per_stack_bonus * stacks
            if stack_bonus:
                bonus += stack_bonus
                notes.append(f"{affix.name}: +{affix.per_stack_bonus} x {stacks} = {stack_bonus}")

    status_bonus = len(target.statuses)
    if status_bonus > 0:
        bonus += status_bonus
        notes.append(f"Target debuffed: +{status_bonus}")

    return bonus, notes


def _apply_enemy_defenses(weapon: Weapon, target: Enemy, damage: int) -> tuple[int, list[str], bool]:
    """Apply defenses in order: armor, dodge, elemental resistance."""
    steps: list[str] = []

    after_armor = max(0, damage - target.armor)
    steps.append(f"Defense A) Armor: {damage} - {target.armor} = {after_armor}")

    if target.try_dodge():
        steps.append("Defense B) Dodge: hidden roll success -> 0")
        return 0, steps, True
    steps.append("Defense B) Dodge: hidden roll fail")

    if DamageTag.ETHEREAL in weapon.all_tags:
        steps.append("Defense C) Elemental resistance ignored by ETHEREAL")
        return after_armor, steps, False

    resist_hits = [tag for tag in weapon.all_tags if tag in target.elemental_resistances]
    resist_pct = min(0.90, 0.10 * len(resist_hits))
    reduced = int(round(after_armor * (1.0 - resist_pct)))
    steps.append(f"Defense C) Elemental resistance: -{int(resist_pct * 100)}% = {reduced}")
    return reduced, steps, False


def _check_condition(condition: str, enemy: Enemy) -> bool:
    """Evaluate existing affix conditions locally for combat pipeline usage."""
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
        return True
    if condition == "first_hit":
        return enemy.times_hit == 0
    return False


def _count_stacks(source: str, enemy: Enemy) -> int:
    """Count stack sources used by per-stack affix bonuses."""
    if source == "debuffs_on_target":
        return len(enemy.statuses)
    if source == "missing_hp_percent":
        missing = enemy.max_hp - enemy.current_hp
        return (missing * 10) // enemy.max_hp
    return 0
