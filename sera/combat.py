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
from sera.elements import ELEMENTS, resistance_modifier


BASE_STAT_DAMAGE = 1
MISS_PATIENCE_SCALE = 0.10
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
            clear_quip = random.choice([
                "That was almost interesting.",
                "Adequate. Next room.",
                "Gone. All of them. Good.",
                "That's how you end a scene.",
                "Cleared. Like a footnote in a history book.",
                "The room is empty. So is my enthusiasm.",
                "Not a survivor among them. As intended.",
                "That's a wipe. Professional, if not exciting.",
                "All targets removed. Moving on.",
                "Another room of dead things. My favorite decor.",
                "The dungeon is lighter by several problems.",
                "Final curtain. Scattered applause. From me. Slowly.",
                "Encounter resolved. Drama: minimal.",
                "That's what a clean sweep looks like. Take notes.",
            ])
            log.append(f'\n  All enemies defeated. "{clear_quip}"')
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
                frozen_quip = random.choice([
                    "Stay still. I like you better this way.",
                    "Ice cold. Like my expectations.",
                    "Don't move. Actually, I prefer it.",
                    "Frozen solid. An improvement.",
                    "Colder than Auril's handshake.",
                    "You make a better statue than a fighter.",
                    "The Spine of the World called. It wants its chill back.",
                    "Preserving you for later disappointment.",
                    "Icewind Dale has warmer welcomes.",
                    "Held. Like a bad thought you can't let go.",
                    "Cryogenic storage. For the useless.",
                    "You're not going anywhere. Good.",
                    "Winter came for you. Specifically you.",
                ])
                log.append(f'\n  {enemy.name} is FROZEN solid! Skipping turn.')
                log.append(f'  Sera: "{frozen_quip}"')
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
                    regen_quip = interest.comment_on_regen(enemy.name)
                    log.append(f"  {enemy.name} regenerates {healed} HP. "
                               f'({enemy.current_hp}/{enemy.max_hp}) "{regen_quip}"')

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
            "It's immune. Wonderful. I love wasting my time.",
            "You brought the wrong toy. Fix it.",
            "Wrong weapon. Think harder.",
            "That bounced off like a compliment off a beholder.",
            "No effect. Like kindness in the Underdark.",
            "The weapon doesn't speak its language.",
            "I just hit nothing. With effort. That's YOUR achievement.",
            "Like throwing snowballs at a white dragon.",
            "Conceptual mismatch. Mortals call it \'being wrong.\'",
            "The enemy doesn't even acknowledge the attempt.",
            "That accomplished exactly nothing. Congratulations.",
            "Even a bag of holding can't contain this failure.",
            "Wrong tool, wrong target, wrong everything.",
        ])
        log.append(f"\n  Sera attacks {target.name} with {weapon.display_name}...")
        missing = target.missing_tag_hint()
        if missing:
            log.append(f'  IMMUNE. Missing tag: [{missing}]. "{immune_quip}"')
        else:
            log.append(f'  IMMUNE. Weapon lacks required tag. "{immune_quip}"')
        log.extend(interest.take_annoyance(5, f'"{target.name} is immune. What a waste of my time."'))
        return log

    # Low-patience miss chance
    patience_ratio = interest.current_patience / interest.max_patience
    miss_chance = max(0.0, (1.0 - patience_ratio) * MISS_PATIENCE_SCALE)
    if random.random() < miss_chance:
        miss_quip = random.choice([
            "I am losing interest.",
            "I'm going through the motions. This is your fault.",
            "That was half-hearted. Even for me.",
            "A blind kobold could have landed that.",
            "My aim falters when I stop caring.",
            "That swing had all the conviction of a suggestion cantrip.",
            "I missed. Not the enemy's doing. Mine. That's worse.",
            "Low effort. Low result. Correlation is not coincidence.",
            "Even my worst should still connect. Apparently not.",
            "The sword moved. The conviction didn't.",
            "A nat one, if you believe in that sort of thing.",
            "Distracted by how boring this is.",
            "I swung. I missed. I'm annoyed. Moving on.",
        ])
        log.append(f"\n  Sera attacks {target.name} with {weapon.display_name}...")
        log.append(f'  MISS. "{miss_quip}"')
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
        interrupt_quip = random.choice([
            "I said shut up.",
            "Nobody asked for your monologue.",
            "Don't point that at her.",
            "That thought? That's where you messed up.",
            "Your concentration breaks. My patience doesn't have to.",
            "Counterspelled. By violence.",
            "Mid-cast cancellation. No refunds.",
            "That was a verbal component. I disagree with it.",
            "Interrupted. Like every Zhentarim scheme.",
            "You were about to do something. Past tense.",
            "Even Karsus knew when to stop casting.",
            "Channel divinity? Channel silence.",
            "I hit you in the middle of your sentence. On purpose.",
            "That ability died in committee.",
        ])
        log.append(f'  {target.name}\'s {interrupted} was INTERRUPTED!')
        log.append(f'  Sera: "{interrupt_quip}" [+5 Patience]')
        interest._restore(5)

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
                "You had a chance. You used it wrong.",
                "Stand still, insect. I need a clear shot.",
                "Nobody asked for a warmup.",
                "Winding up like a catapult in Baldur's Gate. Predictable.",
                "Charging. How dramatic. How slow.",
                "You're building to something. It better be worth it.",
                "A wizard in Thay charges faster than this.",
                "I can feel the ability forming. I can also feel my patience dying.",
                "This delay is costing me more than your ability will cost me.",
                "The dramatic pause was cute. Once.",
                "Concentration check. Mine, not yours.",
                "If I wanted to watch someone charge, I'd visit a war elephant.",
                "You're preparing something big. I'm preparing to leave.",
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
            heal_quip = random.choice([
                "Stop healing. It's dragging on.",
                "Nobody asked for a second act.",
                "You're not broken. You're just stalling.",
                "I will end this personally.",
                "Cure wounds? I'll give you wounds to cure.",
                "Regeneration without permission is rude.",
                "You're duct-taping a sinking ship.",
                "That heal buys you one more hit. From me.",
                "Even a cleric of Ilmater would tell you to give up.",
                "You heal, I hit harder. This is simple arithmetic.",
                "The longer you stall, the worse the ending.",
                "Troll biology. The most annoying school of thought.",
                "Every HP you recover is borrowed time.",
                "Stop. Healing. It's embarrassing for both of us.",
            ])
            log.append(f'  Sera: "{heal_quip}"')

    return log


def _status_quip(effect: StatusEffect) -> str:
    """Sera's commentary on inflicting status effects."""
    quips = {
        StatusEffect.BURNING: random.choice([
            "Burn brighter. Entertain me.",
            "Everything is better on fire.",
            "That's the temperature of my contempt.",
            "Alchemist's fire has nothing on divine spite.",
            "Ablaze. Like Myth Drannor in the bad years.",
            "Ignited. Consider it a housewarming.",
            "Flame wreath. My second-favorite accessory.",
            "Burning alive and still less dramatic than a bard.",
            "Fire doesn't discriminate. Neither do I.",
            "Spontaneous combustion. The best kind.",
            "Hot take: you're on fire.",
            "You'll find the heat accelerates regret.",
            "Burning. Like a scroll nobody read in time.",
        ]),
        StatusEffect.BLEEDING: random.choice([
            "Bleed faster.",
            "Every cut is a promise of something worse.",
            "That's going to leave a mark. Several, actually.",
            "Bleeding out on a dungeon floor. Classic adventurer.",
            "The floor was already red. Now it matches.",
            "Drip. Drip. Drip. Music to my ears.",
            "Blood loss. Nature's hourglass.",
            "You leak. I watch. Fair trade.",
            "Hemorrhaging is just aggressive sharing.",
            "Red is your color. You're wearing a lot of it.",
            "A wound that talks. It says 'you're losing.'",
            "That cut will remember you long after I forget you.",
            "Bleeding is just the body admitting defeat before the mind.",
        ]),
        StatusEffect.SILENCED: random.choice([
            "Finally. Quiet.",
            "Nobody asked for your monologue.",
            "Shut up. I said it once.",
            "Your voice was not your best feature.",
            "Verbal components denied. Permanently.",
            "Even Volo knows when to stop talking.",
            "Silence. The most underrated school of magic.",
            "You had things to say. Past tense.",
            "Words failed you. Now magic does too.",
            "A bard's worst nightmare. My Tuesday.",
            "The best thing you've said all fight: nothing.",
            "Eloquence is overrated. Especially yours.",
            "Muted. Like a bad performance in Waterdeep.",
        ]),
        StatusEffect.CORRODED: random.choice([
            "Your armor was ugly anyway.",
            "Everything corrodes. Some things faster than others.",
            "Science was a mistake. A beautiful mistake.",
            "Acid eats what swords can't reach.",
            "Corrosion: the patient killer.",
            "Your defenses are dissolving. Like your chances.",
            "Rust never sleeps. Neither does contempt.",
            "That armor had a good run. It's over now.",
            "Acid doesn't argue. It just wins.",
            "Structural integrity: compromised. Like your strategy.",
            "Dissolving from the outside in. Philosophically accurate.",
            "Green ooze would approve of this technique.",
            "Your protection melts. My patience doesn't.",
        ]),
        StatusEffect.CURSED: random.choice([
            "Consider this a divine opinion.",
            "You don't touch what belongs to God.",
            "That's not a hex. That's a fact.",
            "A curse from me is a compliment from anyone else.",
            "Cursed. By authority. Mine.",
            "That mark won't wash off. Trust me.",
            "Even Bane's clerics can't undo what I do.",
            "A divine wound that festers. My specialty.",
            "Hexed by a goddess. Put that on your tombstone.",
            "This curse has tenure. It's not leaving.",
            "Shar would be jealous of this darkness.",
            "You've been divinely annotated. In the margins of doom.",
            "That's not bad luck. That's my handwriting.",
        ]),
        StatusEffect.STUNNED: random.choice([
            "Freeze. I wasn't done with you.",
            "Don't move. I need to think.",
            "Stay. I'm not finished.",
            "Paralyzed by divine decree.",
            "That's a hold person. From a hold goddess.",
            "Your nervous system and I had a word.",
            "Stunned. Like a wizard who failed a con save.",
            "Your body disagrees with your brain now.",
            "Complete motor failure. Works as intended.",
            "You stopped moving. Best decision you've made.",
            "Locked in place. Like a bad sculpture.",
            "Neural override. By me.",
            "Standing there like a gargoyle. How fitting.",
        ]),
        StatusEffect.MARKED: random.choice([
            "I see you. You can't hide.",
            "You're mine now. Congratulations.",
            "Marked. That means you're next.",
            "Tagged. Like livestock before market day.",
            "A hunter's mark. Without the hunter. Just the mark.",
            "You glow with divine attention. Pity.",
            "Marked for deletion. From existence.",
            "I've put a pin in you. A divine pin.",
            "That target on your back? It's from me.",
            "You've been chosen. Not in the good way.",
            "Faerûn's most wanted. By me. Specifically.",
            "You're highlighted. Like text in a spellbook.",
            "The mark means I'm coming back. Soon.",
        ]),
        StatusEffect.HUMILIATED: random.choice([
            "That's the face of someone who knows they've lost.",
            "You felt brave for a second. That's adorable.",
            "You're confusing proximity with permission.",
            "Demoralized. Good. Use that feeling.",
            "Even a kobold has more self-respect.",
            "Your confidence evaporates. Like morning dew in Calimshan.",
            "Humbled. By a goddess. At least aim higher next time.",
            "You're not worthy of fear. Just pity.",
            "Dignity: revoked.",
            "Embarrassed in front of the entire dungeon.",
            "Your morale broke before your body did.",
            "Pathetic. Even by mortal standards.",
            "That expression? That's self-awareness arriving late.",
        ]),
        StatusEffect.TERRIFIED: random.choice([
            "Good instinct.",
            "Run if you want. It won't help.",
            "Fear is the only correct response.",
            "Terror is wisdom. You're finally wise.",
            "Even dragons fear something. Today, it's me.",
            "Your survival instincts just woke up. Too late.",
            "Frightened. Like a torchbearer in Tomb of Horrors.",
            "I am the thing in the dark that the dark is afraid of.",
            "That trembling is your body being honest.",
            "Afraid. Good. Afraid is correct.",
            "Your courage had a good run. Two seconds.",
            "The abyss stares back. I stare harder.",
            "Even Demogorgon's cultists know when to run.",
        ]),
        StatusEffect.SLOWED: random.choice([
            "Take your time. Actually, don't.",
            "You're slow. Slower now. Good.",
            "Walk or not at all.",
            "Moving through molasses. Existential molasses.",
            "Speed reduced. Threat level unchanged. Still zero.",
            "Slow as a council meeting in Waterdeep.",
            "Time bends around you. Unfavorably.",
            "Sluggish. Like a rust monster after a big meal.",
            "Crawling now. How dignified.",
            "Your reflexes called in sick.",
            "Haste dispelled. Gravity won.",
            "Moving like you're waist-deep in a swamp. A boring swamp.",
            "Slowed. Every step costs more than the last.",
        ]),
        StatusEffect.WEAKENED: random.choice([
            "Feel that? That's your relevance fading.",
            "Saps their will. Their attacks barely register.",
            "You're not broken. You're just awake.",
            "Enfeebled. Your hits land like suggestions.",
            "Weakness is just honesty about your condition.",
            "You've been ray-of-enfeebled. Without the ray.",
            "Your strength leaves. My patience stays. Barely.",
            "Debilitated. Like a fighter without a magic weapon.",
            "You hit softer now. Which was already soft.",
            "Power drain. I barely notice your attacks now.",
            "Diminished. The mathematical term for 'less annoying.'",
            "Your muscles forgot how to be threatening.",
            "Weak. Like a candle trying to outshine the sun.",
        ]),
        StatusEffect.FROZEN: random.choice([
            "Ice cold. Like my expectations.",
            "One turn of blessed silence.",
            "Stay still. I like you better this way.",
            "Frozen solid. An improvement on your personality.",
            "Suspended in ice. Suspended in irrelevance.",
            "The cold preserves you. For now.",
            "Cryostasis. For the uninteresting.",
            "You make a passable ice sculpture.",
            "Colder than Cania. Less interesting though.",
            "Entombed in frost. My favorite prison.",
            "Winter's grip. Firmer than your resolve.",
            "Locked in a glacier of my contempt.",
            "The ice holds you still. I hold you accountable.",
        ]),
        StatusEffect.DOOMED: random.choice([
            "Tick tock. Enjoy the countdown.",
            "When it fades, you pay.",
            "That thought? That's where you messed up.",
            "Doom is patient. I am not.",
            "The clock is ticking. It's ticking for you.",
            "A sentence has been passed. It detonates.",
            "Doomed. Like every BBEG's plan in act three.",
            "Your expiration date is set. By me.",
            "Countdown to collapse. Enjoy the suspense.",
            "That mark is a promise. I keep promises.",
            "Doomed. The word itself is a spoiler.",
            "When the timer runs out, physics disagrees with your existence.",
            "A delayed verdict. The verdict is 'no.'",
        ]),
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
    if damage > 0 and after_armor == 0:
        after_armor = 1  # minimum damage floor
    steps.append(f"Defense A) Armor: {damage} - {target.armor} = {after_armor}")

    if target.try_dodge():
        steps.append("Defense B) Dodge: hidden roll success -> 0")
        return 0, steps, True
    steps.append("Defense B) Dodge: hidden roll fail")

    if DamageTag.ETHEREAL in weapon.all_tags:
        steps.append("Defense C) Elemental resistance ignored by ETHEREAL")
        return after_armor, steps, False

    weapon_elements = [tag for tag in weapon.all_tags if tag in ELEMENTS]
    defender_elements = list(target.elemental_resistances)

    resist_pct = 0.0
    for atk in weapon_elements:
        for defense in defender_elements:
            resist_pct += resistance_modifier(atk, defense)

    resist_pct = min(0.90, resist_pct)
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
