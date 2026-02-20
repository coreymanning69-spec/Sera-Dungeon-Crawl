#!/usr/bin/env python3
"""
SERA: ENDLESS ENGAGEMENT — Interactive Game

Run this to play the game:
    python3 play.py

Survive 5 floors. Keep Sera interested. Don't be boring.
"""

from __future__ import annotations
import copy
import random

from sera.tags import DamageTag
from sera.weapon import Weapon, Affix
from sera.enemy import Enemy, AnnoyanceType, ANNOYANCE_COST, ANNOYANCE_FLAVOR, defense_key_for_attack
from sera.interest import InterestManager
from sera.status import StatusEffect
from sera.crafting import CraftingMaterial, apply_material, upgrade_weapon
from sera.loader import load_weapons, load_affixes, load_enemies, load_equipment_items
from sera.encounters import generate_encounter, generate_loot_weapon, generate_loot_material, generate_loot_shards
from sera import ui
from sera.stats import PlayerStats
from sera.equipment import EquipmentLoadout, roll_item, EquipmentItem, generate_revision_set


def _build_defense_profile(state: "GameState", stats: PlayerStats | None = None) -> tuple[int, int, dict[str, int]]:
    """Pre-compute defenses used by annoyance-damage calculations."""
    final_stats = stats or state.final_stats
    loadout = state.equipment_loadout
    reduction = loadout.total_damage_reduction() + final_stats.annoyance_reduction()
    resistance = loadout.total_damage_resistance()
    resistances = loadout.total_resistances()
    return reduction, resistance, resistances


# ─────────────────────────────────────────────────────────
# Sera's voice — context-sensitive quips
# ─────────────────────────────────────────────────────────

ATTACK_QUIPS = [
    '"Die faster."',
    '"Was that supposed to be dramatic? It wasn\'t."',
    '"Next."',
    '"Adequate violence."',
    '"Try not to bore me."',
    '"I could do this in my sleep. I have."',
    '"You get one mercy. Did you think you\'d get two?"',
    '"Nice try."',
]

KILL_QUIPS = [
    '"Finally."',
    '"One down. Keep going."',
    '"That was almost satisfying."',
    '"Acceptable."',
    '"You lasted longer than I expected. Low bar."',
    '"Well. That\'s done."',
    '"Fixed."',
]

OVERKILL_QUIPS = [
    '"NOW we\'re talking."',
    '"Excessive? No. Efficient."',
    '"THAT is how you kill something."',
    '"More of that. Less of everything else."',
    '"See? I fix everything."',
]

DODGE_QUIPS = [
    '"Stand still, insect."',
    '"Do that again and I\'m leaving."',
    '"Dodging is for things that fear death. You should."',
    '"Hey. Don\'t ignore me. That\'s rude."',
]

IMMUNE_QUIPS = [
    '"Wrong weapon. Think harder."',
    '"It\'s immune. Wonderful. I love wasting my time."',
    '"You brought the wrong toy. Fix it."',
]

INTERRUPT_QUIPS = [
    '"I said shut up."',
    '"Nobody asked for your monologue."',
    '"Interrupted. You\'re welcome."',
    '"No, no. Only I get to talk that long."',
]

LOW_PATIENCE_QUIPS = [
    '"I\'m running out of reasons to stay."',
    '"This is getting tedious."',
    '"Entertain me or I leave. Simple."',
    '"One more disappointment. That\'s all you get."',
    '"I don\'t think there\'s anything at all that can stop me."',
]

FLOOR_INTRO_QUIPS = [
    '"Let\'s get this over with."',
    '"This better not be boring."',
    '"I sense... mediocrity ahead."',
    '"Show me something new."',
    '"Last chance. Impress me."',
    '"Well, what do you think we should fix first?"',
    '"Smells like... old apples. And blood. But not bad blood. Just scared."',
]

ROOM_CLEAR_QUIPS = [
    '"That was almost interesting."',
    '"Is that all? Really?"',
    '"I expected more. I always do."',
    '"Done. What else do you have?"',
    '"All I see... is fear... and dead men."',
    '"Well. My work here is done."',
]

AUTO_BATTLE_TURNS = 10


def sera_quip(pool: list[str]) -> str:
    return random.choice(pool)


# ─────────────────────────────────────────────────────────
# Run Stats — tracks cumulative stats across a run
# ─────────────────────────────────────────────────────────

class RunStats:
    """Tracks cumulative statistics for a single game run."""
    def __init__(self):
        self.total_damage: int = 0
        self.best_overkill: int = 0
        self.weapons_found: int = 0
        self.materials_used: int = 0

    def record_damage(self, amount: int):
        self.total_damage += amount

    def record_overkill(self, excess: int):
        if excess > self.best_overkill:
            self.best_overkill = excess

    def to_dict(self, state: GameState) -> dict:
        return {
            "floors_cleared": state.floors_cleared,
            "total_kills": state.interest.total_kills,
            "total_turns": state.interest.turn_number,
            "total_damage": self.total_damage,
            "best_overkill": self.best_overkill,
            "weapons_found": self.weapons_found,
            "materials_used": self.materials_used,
            "patience": state.interest.current_patience,
            "max_patience": state.interest.max_patience,
            "weapon_name": state.equipped_weapon.display_name if state.weapons else "",
        }


# ─────────────────────────────────────────────────────────
# Game State
# ─────────────────────────────────────────────────────────

class RunStats:
    """Tracks cumulative run metrics for display."""
    def __init__(self):
        self.total_damage: int = 0
        self.best_overkill: int = 0
        self.weapons_found: int = 0
        self.materials_used: int = 0

    def record_damage(self, amount: int):
        self.total_damage += amount

    def record_overkill(self, excess: int):
        if excess > self.best_overkill:
            self.best_overkill = excess

    def to_dict(self, state: "GameState") -> dict:
        return {
            "total_damage": self.total_damage,
            "best_overkill": self.best_overkill,
            "weapons_found": self.weapons_found,
            "materials_used": self.materials_used,
            "floors_cleared": state.floors_cleared,
            "patience": f"{state.interest.current_patience}/{state.interest.max_patience}",
        }


class GameState:
    def __init__(self):
        self.interest = InterestManager()
        self.floor = 0
        self.max_floors = 5
        self.weapons: list[Weapon] = []
        self.materials: list[CraftingMaterial] = []
        self.upgrade_shards: int = 0
        self.equipped_idx: int = 0
        self.all_enemies = load_enemies()
        self.all_weapons = load_weapons()
        self.all_affixes = load_affixes()
        self.floors_cleared: int = 0
        self.base_stats = PlayerStats()
        self.equipment_loadout = EquipmentLoadout()
        self.equipment_stash: list[EquipmentItem] = []
        self.all_equipment = load_equipment_items()
        self.healing_flasks: int = 2
        self.next_revision_set: list[EquipmentItem] = generate_revision_set(self.all_equipment, floor=1)
        self.revision_set_claimed: bool = False
        self.run_stats: RunStats = RunStats()

    @property
    def equipped_weapon(self) -> Weapon:
        return self.weapons[self.equipped_idx]

    @property
    def final_stats(self) -> PlayerStats:
        return self.equipment_loadout.build_final_stats(self.base_stats)


# ─────────────────────────────────────────────────────────
# Input helpers
# ─────────────────────────────────────────────────────────

def get_choice(prompt: str = "> ", valid: list[str] | None = None) -> str:
    while True:
        choice = ui.get_input(prompt).lower()
        if choice in ("quit", "q"):
            return "quit"
        if valid is None or choice in valid:
            return choice
        print(f'  Invalid. Options: {", ".join(valid)}')


def pause(msg: str = "  [Press Enter]"):
    ui.get_input(msg)


# ─────────────────────────────────────────────────────────
# Title screen
# ─────────────────────────────────────────────────────────

def title_screen() -> str:
    """Returns 'new_game', 'simulation', or 'quit'."""
    ui.clear()
    print(ui.render_title_screen())
    choice = get_choice("> ", ["1", "2", "3"])
    if choice in ("quit", "3"):
        return "quit"
    if choice == "2":
        return "simulation"
    return "new_game"


# ─────────────────────────────────────────────────────────
# Weapon selection at game start
# ─────────────────────────────────────────────────────────

def choose_starting_weapon(state: GameState):
    ui.clear()
    # Build guaranteed diverse starting options covering the 3 major vulnerability types:
    #   Slot 1: DIVINE or ETHEREAL (counters spirits/ghosts on floors 3-4)
    #   Slot 2: HEAVY (counters armored enemies) — biased toward high-dmg weapons
    #   Slot 3: ARCANE (counters constructs and bosses on floor 5)
    # This ensures the player always has a viable tool for every gate in the dungeon.
    divine_ethereal_pool = [w for w in state.all_weapons
                            if DamageTag.DIVINE in w.tags or DamageTag.ETHEREAL in w.tags]
    heavy_pool = [w for w in state.all_weapons
                  if w.base_damage >= 3 or DamageTag.HEAVY in w.tags]
    arcane_pool = [w for w in state.all_weapons if DamageTag.ARCANE in w.tags]

    options: list = []
    used_names: set[str] = set()

    def _pick(pool: list) -> bool:
        available = [w for w in pool if w.name not in used_names]
        if not available:
            return False
        pick = random.choice(available)
        options.append(pick)
        used_names.add(pick.name)
        return True

    _pick(divine_ethereal_pool)  # slot 1: spirit-killer
    _pick(heavy_pool)            # slot 2: armor-breaker
    _pick(arcane_pool)           # slot 3: construct/boss counter

    # Fill to 3 if any pool was empty or exhausted
    remaining = [w for w in state.all_weapons if w.name not in used_names]
    while len(options) < 3 and remaining:
        pick = random.choice(remaining)
        options.append(pick)
        remaining = [w for w in remaining if w.name != pick.name]

    if not options:
        options = random.sample(state.all_weapons, min(3, len(state.all_weapons)))
    random.shuffle(options)

    lines = [
        ui.box_top(),
        ui.box_line("░▒▓█ CHOOSE YOUR WEAPON █▓▒░", "center"),
        ui.box_divider(),
        ui.box_line('Sera: "Fine. What are we working with?"'),
        ui.box_blank(),
    ]
    for i, w in enumerate(options):
        tag_str = ", ".join(t.name for t in w.all_tags)
        lines.append(ui.box_line(f"  ▸ [{i+1}] {w.name} ({w.base_damage} dmg) [{tag_str}]"))
        lines.append(ui.box_line(f'        "{w.flavor}"'))
    lines.append(ui.box_blank())
    lines.append(ui.box_bot())
    print("\n".join(lines))

    valid = [str(i+1) for i in range(len(options))]
    choice = get_choice("> ", valid)
    if choice == "quit":
        return False

    picked = copy.deepcopy(options[int(choice) - 1])
    state.weapons.append(picked)
    state.equipped_idx = 0

    ui.clear()
    print(ui.box_top())
    print(ui.box_line(f'Sera picks up the {picked.name}.', "center"))
    print(ui.box_line(f'"{picked.flavor}"', "center"))
    print(ui.box_bot())
    pause()
    return True


# ─────────────────────────────────────────────────────────
# Commands menu (debug/cheat commands)
# ─────────────────────────────────────────────────────────

def _show_commands_menu(state: GameState, enemies: list[Enemy]):
    """Show cheat/debug commands menu."""
    ui.clear()
    print(ui.box_top())
    print(ui.box_line("░▒▓█ COMMANDS MENU █▓▒░", "center"))
    print(ui.box_line('Sera: "Cheating? How refreshingly honest."', "center"))
    print(ui.box_divider())
    print(ui.box_line("  ▸ [1] GetItem <item_name> - Add item to inventory"))
    print(ui.box_line("  ▸ [2] FightMonster <name> - Spawn specific enemy"))
    print(ui.box_line("  ▸ [3] SetHP <amount> - Set current Patience"))
    print(ui.box_line("  ▸ [4] SetDMG <amount> - Set weapon base damage"))
    print(ui.box_line("  ▸ [5] SetSTR <amount> - Set STR stat"))
    print(ui.box_line("  ▸ [6] SetAP <amount> - Set AP stat"))
    print(ui.box_line("  ▸ [0] Back to combat"))
    print(ui.box_blank())
    print(ui.box_bot())

    choice = get_choice("> ", ["1", "2", "3", "4", "5", "6", "0"])
    if choice in ("0", "quit"):
        return

    if choice == "1":
        _cmd_get_item(state)
    elif choice == "2":
        _cmd_fight_monster(state, enemies)
    elif choice == "3":
        _cmd_set_hp(state)
    elif choice == "4":
        _cmd_set_dmg(state)
    elif choice == "5":
        _cmd_set_str(state)
    elif choice == "6":
        _cmd_set_ap(state)

    pause()


def _cmd_get_item(state: GameState):
    """Cheat command: Get a weapon or material by name."""
    print("  Available weapons:")
    for i, w in enumerate(state.all_weapons[:5]):
        print(f"    [{i+1}] {w.name}")
    print("  Available materials:")
    for i, m in enumerate(state.materials if state.materials else []):
        print(f"    [M{i+1}] {m.name}")

    item_name = ui.get_input("  Item name > ")
    if not item_name:
        return

    # Try to find weapon
    for w in state.all_weapons:
        if w.name.lower() == item_name.lower():
            new_weapon = copy.deepcopy(w)
            state.weapons.append(new_weapon)
            print(f'  Added {new_weapon.name}! Sera: "Interesting choice."')
            return

    print(f'  Item "{item_name}" not found. Sera: "You can\'t even cheat correctly."')


def _cmd_fight_monster(state: GameState, enemies: list[Enemy]):
    """Cheat command: Spawn a specific enemy."""
    print("  Available enemy archetypes:")
    seen_names = set()
    for e in state.all_enemies:
        if e.name not in seen_names:
            print(f"    - {e.name} ({e.archetype})")
            seen_names.add(e.name)

    monster_name = ui.get_input("  Monster name > ")
    if not monster_name:
        return

    for e in state.all_enemies:
        if e.name.lower() == monster_name.lower():
            new_enemy = copy.deepcopy(e)
            enemies.append(new_enemy)
            print(f'  Spawned {new_enemy.name}! Sera: "More toys to break."')
            return

    print(f'  Monster "{monster_name}" not found.')


def _cmd_set_hp(state: GameState):
    """Cheat command: Set Patience."""
    amount_str = ui.get_input("  Set Patience to > ")
    try:
        amount = int(amount_str)
        state.interest.current_patience = max(0, min(amount, state.interest.max_patience))
        print(f'  Patience set to {state.interest.current_patience}. Sera: "How generous of you."')
    except ValueError:
        print('  Invalid number. Sera: "Try using actual numbers."')


def _cmd_set_dmg(state: GameState):
    """Cheat command: Set weapon base damage."""
    amount_str = ui.get_input("  Set base damage to > ")
    try:
        amount = int(amount_str)
        state.equipped_weapon.base_damage = max(1, min(amount, 30))
        print(f'  Base damage set to {state.equipped_weapon.base_damage}. Sera: "Now we\'re talking."')
    except ValueError:
        print('  Invalid number.')


def _cmd_set_str(state: GameState):
    """Cheat command: Set STR stat."""
    amount_str = ui.get_input("  Set STR to > ")
    try:
        amount = int(amount_str)
        state.base_stats.values["STR"] = max(0, amount)
        print(f'  STR set to {state.base_stats.values["STR"]}.')
    except ValueError:
        print('  Invalid number.')


def _cmd_set_ap(state: GameState):
    """Cheat command: Set AP stat."""
    amount_str = ui.get_input("  Set AP to > ")
    try:
        amount = int(amount_str)
        state.base_stats.values["AP"] = max(0, amount)
        print(f'  AP set to {state.base_stats.values["AP"]}.')
    except ValueError:
        print('  Invalid number.')


# ─────────────────────────────────────────────────────────
# Interactive combat
# ─────────────────────────────────────────────────────────

def run_combat(state: GameState, enemies: list[Enemy]) -> bool:
    """
    Interactive combat loop.
    Returns True if Sera survived, False if game over.
    """
    interest = state.interest
    weapon = state.equipped_weapon
    combat_turn = 0

    while True:
        alive = [e for e in enemies if e.current_hp > 0]
        if not alive:
            _show_room_clear(interest)
            return True

        if interest.game_over:
            return False

        combat_turn += 1
        interest.turn_number += 1
        interest._kills_this_turn = 0

        # Passive drain
        interest._drain(interest.TICK_DRAIN, "Time passes.")
        if interest.game_over:
            return False

        # --- PLAYER TURN ---
        alive = [e for e in enemies if e.current_hp > 0]
        ui.clear()
        print(ui.render_combat_hud(combat_turn, weapon, enemies, interest, state.final_stats, state.healing_flasks))

        # Patience-based commentary
        if interest.current_patience <= 20:
            print(f"  Sera: {sera_quip(LOW_PATIENCE_QUIPS)}")
        else:
            print(f'  Sera: "{interest._time_quip()}"')
        print(f"  [-1 Patience] Time ticks.")
        print()

        # Get player action
        valid_actions = [str(i+1) for i in range(len(alive))] + ["i", "w", "h", "a", "0"]
        action = None
        while action is None:
            choice = get_choice("  Your move > ", valid_actions)
            if choice == "quit":
                return False
            if choice == "0":
                _show_commands_menu(state, enemies)
                ui.clear()
                print(ui.render_combat_hud(combat_turn, weapon, enemies, interest, state.final_stats, state.healing_flasks))
                continue
            if choice == "i":
                _do_inspect(alive, combat_turn, weapon, enemies, interest, state)
                continue
            if choice == "w":
                ui.clear()
                print(ui.render_weapon_detail(weapon))
                pause()
                ui.clear()
                print(ui.render_combat_hud(combat_turn, weapon, enemies, interest, state.final_stats, state.healing_flasks))
                continue
            if choice == "h":
                _use_healing_flask(state)
                if interest.game_over:
                    return False
                pause()
                ui.clear()
                print(ui.render_combat_hud(combat_turn, weapon, enemies, interest, state.final_stats, state.healing_flasks))
                continue
            if choice == "a":
                turns_run = _run_auto_battle_burst(state, enemies, AUTO_BATTLE_TURNS)
                combat_turn += max(0, turns_run - 1)
                if interest.game_over:
                    return False
                if not any(e.current_hp > 0 for e in enemies):
                    _show_room_clear(interest)
                    return True
                pause()
                action = None
                continue
            action = int(choice) - 1

        target = alive[action]

        # --- RESOLVE ATTACK ---
        print()
        _resolve_player_attack(weapon, target, interest, state.final_stats, state.run_stats)
        pause()

        if interest.game_over:
            return False

        # --- ENEMY PHASE ---
        alive = [e for e in enemies if e.current_hp > 0]
        defense_profile = _build_defense_profile(state)
        for enemy in alive:
            if interest.game_over:
                return False
            if enemy.is_frozen():
                ui.clear()
                print(ui.box_top())
                print(ui.box_line(f"░░ {enemy.name} is FROZEN! ░░", "center"))
                print(ui.box_line('Sera: "Stay still. I like you better this way."', "center"))
                print(ui.box_bot())
                pause()
                continue
            _resolve_enemy_action(enemy, state, defense_profile)

            if interest.game_over:
                return False

        # --- DOT PHASE ---
        for enemy in enemies:
            if enemy.current_hp > 0:
                hp_before_dot = enemy.current_hp
                dot_total, dot_log = enemy.tick_dot_damage()
                if dot_log:
                    kill_name = enemy.name if enemy.current_hp <= 0 else None
                    ui.clear()
                    print(ui.render_dot_tick(dot_log, kill_name))
                    if kill_name:
                        kill_log = interest.register_kill(
                            enemy.name, dot_total, hp_before_dot)
                        print(ui.render_kill_report(enemy.name, kill_log))
                        state.run_stats.record_damage(dot_total)
                    pause()

        # --- CLEANUP PHASE ---
        for enemy in enemies:
            if enemy.current_hp > 0:
                status_log, kill_events = enemy.tick_statuses()
                if status_log:
                    # Show any detonations or expirations
                    for line in status_log:
                        if "DOOM" in line or "destroyed" in line:
                            ui.clear()
                            print(ui.box_top())
                            print(ui.box_line("░░ DOOM DETONATES ░░", "center"))
                            print(ui.box_line(line.strip(), "center"))
                            print(ui.box_bot())
                            pause()
                for event in kill_events:
                    kill_log = interest.register_kill(
                        event.enemy_name,
                        event.damage_dealt,
                        event.enemy_hp_was,
                    )
                    print(ui.render_kill_report(event.enemy_name, kill_log))
                    pause()
                enemy.tick_cooldowns()
                healed = enemy.tick_regen()
                if healed > 0:
                    ui.clear()
                    print(ui.box_top())
                    print(ui.box_line(f"{enemy.name} regenerates {healed} HP!", "center"))
                    print(ui.box_line(f"HP: {ui.hp_bar(enemy.current_hp, enemy.max_hp, 15)}", "center"))
                    print(ui.box_line(f'Sera: "Stop healing. It\'s dragging on."', "center"))
                    print(ui.box_bot())
                    pause()


def _show_room_clear(interest: InterestManager):
    ui.clear()
    print(ui.box_top())
    print(ui.box_line("░▒▓█ ROOM CLEARED █▓▒░", "center"))
    print(ui.box_line(sera_quip(ROOM_CLEAR_QUIPS), "center"))
    print(ui.box_line(f"Patience: {ui.patience_bar(interest)}", "center"))
    print(ui.box_bot())
    pause()


def _do_inspect(alive, combat_turn, weapon, enemies, interest, state):
    if len(alive) == 1:
        inspect_idx = 0
    else:
        print(f"  Which enemy? [1-{len(alive)}]")
        ic = get_choice("  > ", [str(i+1) for i in range(len(alive))])
        if ic == "quit":
            return
        inspect_idx = int(ic) - 1
    ui.clear()
    print(ui.render_inspect(alive[inspect_idx]))
    pause()
    ui.clear()
    print(ui.render_combat_hud(combat_turn, weapon, enemies, interest, state.final_stats, state.healing_flasks))


def _resolve_player_attack(weapon: Weapon, target: Enemy, interest: InterestManager, stats: PlayerStats, run_stats: RunStats | None = None):
    """Full attack resolution with dodge, permission, interrupt, damage."""

    # --- Permission Check ---
    if not target.check_permission(weapon.all_tags):
        print(f'  Sera attacks {target.name} with {weapon.display_name}...')
        print(f'  IMMUNE. Weapon lacks required tag.')
        print(f'  Sera: {sera_quip(IMMUNE_QUIPS)}')
        ann_log = interest.take_annoyance(5, f"{target.name} is immune")
        for line in ann_log:
            print(f"  {line.strip()}")
        return

    # --- Miss Chance (based on low Patience) ---
    # As Patience drops, Sera cares less about accuracy
    patience_ratio = interest.current_patience / interest.max_patience
    miss_chance = max(0, (1.0 - patience_ratio) * 0.25)  # Up to 25% miss at 0 patience
    if random.random() < miss_chance:
        ui.clear()
        print(ui.box_top())
        for art_line in ["   ~  ~  ~", "  ~  MISS  ~", "   ~  ~  ~"]:
            print(ui.box_line(art_line, "center"))
        print(ui.box_line("░░ SERA MISSES! ░░", "center"))
        print(ui.box_divider())
        print(ui.box_line(f"  Sera swings at {target.name}... and misses completely!"))
        print(ui.box_line(f'  Sera: "I don\'t even care anymore."'))
        print(ui.box_line(f"  Low Patience = {int(miss_chance * 100)}% miss chance"))
        print(ui.box_line(f"  [-1 Patience] Frustration"))
        print(ui.box_bot())
        interest._drain(1, "Miss due to low patience")
        return

    # --- Dodge Roll ---
    if target.try_dodge():
        ui.clear()
        print(ui.render_dodge(target.name))
        interest._drain(2, "Dodge")
        return

    # --- Interrupt Check (hitting a casting enemy cancels their charge) ---
    interrupted = target.interrupt_cast()
    if interrupted:
        ui.clear()
        print(ui.render_interrupt(target.name, interrupted))
        interest._restore(3)
        print(f"  Sera: {sera_quip(INTERRUPT_QUIPS)}")
        pause()

    # --- Damage Calculation ---
    damage, steps = weapon.calculate_damage(target)
    stat_bonus = stats.attack_bonus()
    if stat_bonus > 0:
        pre_stat = damage
        damage = min(30, damage + stat_bonus)
        steps.append(f"  + {stat_bonus} (stats: STR/AP) = {pre_stat + stat_bonus}")
        if damage < pre_stat + stat_bonus:
            steps.append("  [Clamped to 30]")
    steps.append(f"Final (clamped 0-30): {damage}")
    hp_before = target.current_hp
    actual, dead = target.take_damage(damage)
    armor_absorbed = damage - actual if damage > actual else 0

    if run_stats:
        run_stats.record_damage(actual)

    print(ui.render_damage_report(steps, target.name, actual, armor_absorbed))

    # Attack quip
    if not dead:
        print(f"  Sera: {sera_quip(ATTACK_QUIPS)}")

    # Apply statuses from affixes
    for affix in [weapon.prefix, weapon.suffix, weapon.set_bonus]:
        if affix and affix.inflicts_status:
            effect = StatusEffect[affix.inflicts_status]
            target.apply_status(effect, affix.status_duration, affix.status_potency)
            print(f'  Applied {effect.name}!')

    print(f"  {target.name}: {ui.hp_bar(target.current_hp, target.max_hp, 15)}")

    # --- Kill ---
    if dead:
        kill_log = interest.register_kill(target.name, damage, hp_before)
        print()
        print(f"  Sera: {sera_quip(KILL_QUIPS)}")
        # Check for overkill
        excess = max(0, damage - hp_before)
        if excess > 0:
            if run_stats:
                run_stats.record_overkill(excess)
            print(f"  Sera: {sera_quip(OVERKILL_QUIPS)}")
            run_stats.record_overkill(excess)
        print(ui.render_kill_report(target.name, kill_log))


def _run_auto_battle_burst(state: GameState, enemies: list[Enemy], max_turns: int) -> int:
    """Run a quick auto-battle burst and print a compact turn-by-turn summary."""
    interest = state.interest
    weapon = state.equipped_weapon
    stats = state.final_stats
    turns_run = 0

    # Track stats for summary table
    total_damage_dealt = 0
    total_kills = 0
    total_patience_lost = 0
    turn_results = []

    ui.clear()
    print(ui.box_top())
    print(ui.box_line(f"░▒▓█ AUTO-BATTLE ({max_turns} TURNS MAX) █▓▒░", "center"))
    print(ui.box_line('Sera: "Fine. I\'ll do it myself for a bit."', "center"))
    print(ui.box_divider())

    for _ in range(max_turns):
        alive = [e for e in enemies if e.current_hp > 0]
        if not alive or interest.game_over:
            break

        turns_run += 1
        interest.turn_number += 1
        interest._kills_this_turn = 0
        patience_before_turn = interest.current_patience
        interest._drain(interest.TICK_DRAIN, "Time passes.")
        print(ui.box_line(f"Turn {interest.turn_number}: -1 Patience (time)"))
        if interest.game_over:
            break

        turn_damage = 0
        turn_kills = 0

        target = alive[0]
        damage, _steps = weapon.calculate_damage(target)
        damage = min(30, damage + stats.attack_bonus())
        hp_before = target.current_hp
        actual, dead = target.take_damage(damage)
        turn_damage += actual
        total_damage_dealt += actual
        print(ui.box_line(f"  Attack {target.name}: {actual} damage ({target.current_hp}/{target.max_hp})"))

        for affix in [weapon.prefix, weapon.suffix, weapon.set_bonus]:
            if affix and affix.inflicts_status:
                effect = StatusEffect[affix.inflicts_status]
                target.apply_status(effect, affix.status_duration, affix.status_potency)

        if dead:
            interest.register_kill(target.name, damage, hp_before)
            turn_kills += 1
            total_kills += 1
            print(ui.box_line(f"  {target.name} defeated. Patience now {interest.current_patience}."))

        reduction, resistance, resistances = _build_defense_profile(state, stats)
        for enemy in [e for e in enemies if e.current_hp > 0]:
            if enemy.is_frozen():
                print(ui.box_line(f"  {enemy.name} is frozen and skips."))
                continue
            ability = enemy.choose_action()
            if ability is None:
                if enemy.is_casting and enemy.pending_ability:
                    print(ui.box_line(f"  {enemy.name} charges {enemy.pending_ability.name}."))
                continue

            base_cost = ANNOYANCE_COST[ability.annoyance]
            mult = enemy.get_annoyance_multiplier()
            pre_mitigation = max(1, int(base_cost * mult))
            attack_type = defense_key_for_attack(ability.attack_type)
            elem_res = resistances.get(attack_type, 0)
            mitigated = max(1, pre_mitigation - reduction)
            resist_pct = min(0.75, (resistance + elem_res) / 100)
            cost = max(1, int(round(mitigated * (1 - resist_pct))))
            interest.take_annoyance(cost, ability.name)
            print(ui.box_line(f"  {enemy.name} uses {ability.name} [{attack_type}]: -{cost} Patience"))
            if interest.game_over:
                break

        if interest.game_over:
            break

        for enemy in enemies:
            if enemy.current_hp <= 0:
                continue
            hp_before_dot = enemy.current_hp
            dot_total, _ = enemy.tick_dot_damage()
            if dot_total > 0:
                print(ui.box_line(f"  DOT on {enemy.name}: {dot_total} ({enemy.current_hp}/{enemy.max_hp})"))
            if enemy.current_hp <= 0:
                interest.register_kill(enemy.name, dot_total, hp_before_dot)
                continue

            _status_log, kill_events = enemy.tick_statuses()
            for event in kill_events:
                interest.register_kill(event.enemy_name, event.damage_dealt, event.enemy_hp_was)
                print(ui.box_line(f"  {event.enemy_name} destroyed by status detonation."))

            enemy.tick_cooldowns()
            healed = enemy.tick_regen()
            if healed > 0:
                print(ui.box_line(f"  {enemy.name} regenerates {healed}."))

        patience_after_turn = interest.current_patience
        patience_delta = patience_after_turn - patience_before_turn
        total_patience_lost += abs(min(0, patience_delta))

        turn_results.append({
            "turn": interest.turn_number,
            "damage": turn_damage,
            "kills": turn_kills,
            "patience": f"{patience_after_turn}/{interest.max_patience}",
        })

        print(ui.box_line(f"  End Patience: {interest.current_patience}/{interest.max_patience}"))
        print(ui.box_divider_thin())

    # Display summary table
    print(ui.box_divider())
    print(ui.box_header("AUTO-BATTLE SUMMARY"))
    print(ui.box_divider_thin())
    print(ui.box_line(f"  {'Turn':<8} {'Damage':<10} {'Kills':<8} {'Patience':<20}"))
    print(ui.box_divider_thin())
    for result in turn_results[-5:]:  # Show last 5 turns
        print(ui.box_line(f"  {result['turn']:<8} {result['damage']:<10} {result['kills']:<8} {result['patience']:<20}"))
    print(ui.box_divider())
    print(ui.box_line(f"  Total Turns: {turns_run}"))
    print(ui.box_line(f"  Total Damage Dealt: {total_damage_dealt}"))
    print(ui.box_line(f"  Total Kills: {total_kills}"))
    print(ui.box_line(f"  Final Patience: {interest.current_patience}/{interest.max_patience}"))
    print(ui.box_blank())
    print(ui.box_line(f"Auto-battle complete.", "center"))
    print(ui.box_bot())
    return turns_run


def _resolve_enemy_action(
    enemy: Enemy,
    state: GameState,
    defense_profile: tuple[int, int, dict[str, int]] | None = None,
):
    """Resolve one enemy's turn with defensive bonuses from equipment/stats."""
    interest = state.interest
    ability = enemy.choose_action()

    if ability is None:
        if enemy.is_casting and enemy.pending_ability:
            remaining = enemy.cast_turns_remaining
            ui.clear()
            print(ui.box_top())
            print(ui.box_line(f"{enemy.name} is charging...", "center"))
            print(ui.box_line(
                f"{enemy.pending_ability.name} "
                f"({remaining} turn{'s' if remaining != 1 else ''} left)",
                "center"))
            print(ui.box_line('Sera: "Hurry up or I\'m leaving."', "center"))
            print(ui.box_bot())
            pause()
        return

    base_cost = ANNOYANCE_COST[ability.annoyance]
    mult = enemy.get_annoyance_multiplier()
    pre_mitigation = max(1, int(base_cost * mult))

    reduction, resistance, resistances = defense_profile or _build_defense_profile(state)
    attack_type = defense_key_for_attack(ability.attack_type)
    elem_res = resistances.get(attack_type, 0)

    mitigated = max(1, pre_mitigation - reduction)
    resist_pct = min(0.75, (resistance + elem_res) / 100)
    cost = max(1, int(round(mitigated * (1 - resist_pct))))

    flavor = ability.flavor or ANNOYANCE_FLAVOR[ability.annoyance]

    ui.clear()
    print(ui.render_enemy_action(enemy, f"{ability.name} [{attack_type}]", flavor, cost))
    if mult < 1.0:
        print(f"  (WEAKENED: {base_cost} -> {pre_mitigation} patience drain)")
    if reduction > 0 or resistance > 0 or elem_res > 0:
        print(f"  Defensive bonuses: -{reduction} flat, -{resistance}% general, -{elem_res}% {attack_type.title()}.")
    interest.take_annoyance(cost, f"{ability.name}")

    # HEAL_SELF abilities actually heal the enemy
    if ability.annoyance == AnnoyanceType.HEAL_SELF:
        heal_amount = min(5, enemy.max_hp - enemy.current_hp)
        if heal_amount > 0:
            enemy.current_hp += heal_amount
            print(ui.box_top())
            print(ui.box_line(f"{enemy.name} heals {heal_amount} HP!", "center"))
            print(ui.box_line(f"HP: {ui.hp_bar(enemy.current_hp, enemy.max_hp, 15)}", "center"))
            print(ui.box_line('Sera: "Stop healing. It\'s dragging on."', "center"))
            print(ui.box_bot())

    print(f"  Patience: {ui.patience_bar(interest)}")
    pause()




def _use_healing_flask(state: GameState):
    interest = state.interest
    if state.healing_flasks <= 0:
        print('  No healing flasks left. "Try not to disappoint me instead."')
        return
    if interest.current_patience >= interest.max_patience:
        print('  Patience already full. "I am already perfectly entertained."')
        return

    heal = state.final_stats.healing_power()
    for item in state.equipment_loadout.equipped.values():
        if item and "Second Wind" in (item.ability or ""):
            heal += 2

    before = interest.current_patience
    interest._restore(heal)
    state.healing_flasks -= 1
    gained = interest.current_patience - before
    print(f"  Used Healing Flask: +{gained} Patience ({interest.current_patience}/{interest.max_patience})")
    print('  Sera: "Better. Keep the momentum."')


# ─────────────────────────────────────────────────────────
# Loot phase
# ─────────────────────────────────────────────────────────

def loot_phase(state: GameState):
    """Offer loot after clearing a room."""
    weapon_drop = generate_loot_weapon(state.floor, state.all_weapons, state.all_affixes)
    material_drop = generate_loot_material()
    shard_drop = generate_loot_shards(state.floor)
    equipment_drop = roll_item(random.choice(state.all_equipment)) if state.all_equipment and random.random() < 0.55 else None

    ui.clear()
    screen, choices = ui.render_loot_screen(
        weapon_drop, material_drop, state.interest, shard_drop)
    print(screen)

    # Auto-collect shards
    if shard_drop > 0:
        state.upgrade_shards += shard_drop
        print(f'  Collected {shard_drop} Upgrade Shard{"s" if shard_drop != 1 else ""}!')
        print(f'  Total shards: {state.upgrade_shards}')
        print(f'  Sera: "Shiny. Useful."')
        print()

    if equipment_drop:
        print(f"  [E] Found equipment: {equipment_drop.name} ({equipment_drop.slot}) {equipment_drop.ascii_art}")
        print(f"      Bonuses: {equipment_drop.stat_bonuses} | DR {equipment_drop.damage_reduction} | RES {equipment_drop.damage_resistance}%")
        if equipment_drop.resistances:
            print(f"      Elemental: {equipment_drop.resistances}")
        print(f"      Ability: {equipment_drop.ability}")
        c = get_choice("  Take equipment? [y/n] > ", ["y", "n"])
        if c == "y":
            state.equipment_stash.append(equipment_drop)
            print('  Sera: "Finally, something wearable."')
        else:
            print('  Sera: "Then leave it to rust."')

    if not choices:
        pause()
        return

    for kind, idx in choices:
        if kind == "weapon":
            print(f"  [{idx}] Take {weapon_drop.display_name}?  [y/n]")
            c = get_choice("  > ", ["y", "n"])
            if c == "y":
                state.weapons.append(weapon_drop)
                state.run_stats.weapons_found += 1
                print(f'  Sera: "This might be useful."')
            else:
                print(f'  Sera: "Trash."')

        if kind == "material":
            print(f"  [{idx}] Take {material_drop.name}?  [y/n]")
            c = get_choice("  > ", ["y", "n"])
            if c == "y":
                state.materials.append(material_drop)
                print(f'  Sera: "I\'ll hold onto this."')
            else:
                print(f'  Sera: "I have standards."')

    pause()


# ─────────────────────────────────────────────────────────
# Between-floor menu
# ─────────────────────────────────────────────────────────

def between_floors(state: GameState) -> bool:
    """
    Between-floor menu: equip, craft, upgrade, view inventory, or continue.
    Returns False if player quits.
    """
    while True:
        ui.clear()
        print(ui.render_between_floors(
            state.floor, state.interest, state.upgrade_shards, state.healing_flasks,
            state.next_revision_set, state.revision_set_claimed))

        choice = get_choice("> ", ["1", "2", "3", "4", "5", "6", "7", "8", "9"])
        if choice in ("quit", "9"):
            return False

        if choice == "1":
            return True

        if choice == "2":
            equip_screen(state)

        if choice == "3":
            craft_screen(state)

        if choice == "4":
            upgrade_screen(state)

        if choice == "5":
            ui.clear()
            print(ui.render_inventory(
                state.weapons, state.materials, state.equipped_idx,
                state.upgrade_shards, state.equipment_stash, state.final_stats))
            pause()

        if choice == "6":
            equipment_screen(state)

        if choice == "7":
            claim_revision_set(state)

        if choice == "8":
            ui.clear()
            print(ui.render_run_stats(state.run_stats.to_dict(state)))
            pause()

        if choice == "5":
            ui.clear()
            print(ui.render_run_stats(state.run_stats.to_dict(state)))
            pause()


def equip_screen(state: GameState):
    if len(state.weapons) < 2:
        ui.clear()
        print(ui.box_top())
        print(ui.box_line("Only one weapon.", "center"))
        print(ui.box_line('"It\'s not like I have options."', "center"))
        print(ui.box_bot())
        pause()
        return

    ui.clear()
    print(ui.render_equip_screen(state.weapons, state.equipped_idx))
    valid = [str(i+1) for i in range(len(state.weapons))] + ["0"]
    choice = get_choice("> ", valid)
    if choice in ("0", "quit"):
        return
    idx = int(choice) - 1
    state.equipped_idx = idx
    w = state.weapons[idx]
    print(f'  Equipped: {w.display_name}')
    print(f'  Sera: "This will do."')
    pause()


def equipment_screen(state: GameState):
    while True:
        ui.clear()
        print(ui.render_equipment_menu(state.equipment_loadout, state.equipment_stash, state.final_stats))
        if not state.equipment_stash:
            pause()
            return

        valid = [str(i+1) for i in range(len(state.equipment_stash))] + ["0"]
        choice = get_choice("  Equip item # (or 0 to leave) > ", valid)
        if choice in ("0", "quit"):
            return

        idx = int(choice) - 1
        item = state.equipment_stash.pop(idx)
        old = state.equipment_loadout.equip(item)
        if old:
            state.equipment_stash.append(old)
            print(f"  Replaced {old.name} with {item.name} in [{item.slot}].")
        else:
            print(f"  Equipped {item.name} in [{item.slot}].")
        print('  Sera: "That had better look good in motion."')
        pause()


def craft_screen(state: GameState):
    if not state.materials:
        ui.clear()
        print(ui.box_top())
        print(ui.box_line("No materials.", "center"))
        print(ui.box_line('"Find me something to work with."', "center"))
        print(ui.box_bot())
        pause()
        return

    ui.clear()
    print(ui.render_craft_screen(state.weapons, state.materials, state.equipped_idx))

    print("  Apply material to which weapon?")
    valid_w = [str(i+1) for i in range(len(state.weapons))] + ["0"]
    wc = get_choice("  Weapon > ", valid_w)
    if wc in ("0", "quit"):
        return
    w_idx = int(wc) - 1

    print("  Which material?")
    valid_m = [str(i+1) for i in range(len(state.materials))] + ["0"]
    mc = get_choice("  Material > ", valid_m)
    if mc in ("0", "quit"):
        return
    m_idx = int(mc) - 1

    weapon = state.weapons[w_idx]
    material = state.materials[m_idx]

    craft_log = apply_material(weapon, material)
    state.materials.pop(m_idx)
    state.run_stats.materials_used += 1

    ui.clear()
    print(ui.box_top())
    print(ui.box_line("░▒▓█ CRAFTING █▓▒░", "center"))
    print(ui.box_divider())
    for line in craft_log:
        print(ui.box_line(line.strip()))
    print(ui.box_divider_pixel())
    print(ui.box_bot())
    pause()


def upgrade_screen(state: GameState):
    if state.upgrade_shards <= 0:
        print('  No upgrade shards. "Kill things and find some."')
        pause()
        return

    ui.clear()
    print(ui.render_upgrade_screen(state.weapons, state.equipped_idx, state.upgrade_shards))

    print("  Upgrade which weapon?")
    valid = [str(i+1) for i in range(len(state.weapons))] + ["0"]
    choice = get_choice("  > ", valid)
    if choice in ("0", "quit"):
        return

    w_idx = int(choice) - 1
    weapon = state.weapons[w_idx]

    upgrade_log, shards_used = upgrade_weapon(weapon, state.upgrade_shards)
    state.upgrade_shards -= shards_used

    ui.clear()
    print(ui.box_top())
    if shards_used > 0:
        print(ui.box_line("░▒▓█ UPGRADE COMPLETE █▓▒░", "center"))
    else:
        print(ui.box_line("░▒▓█ UPGRADE FAILED █▓▒░", "center"))
    print(ui.box_divider())
    for line in upgrade_log:
        print(ui.box_line(line.strip()))
    print(ui.box_line(f"  Shards remaining: {state.upgrade_shards}"))
    print(ui.box_divider_pixel())
    print(ui.box_bot())
    pause()


def claim_revision_set(state: GameState):
    if state.revision_set_claimed:
        print('  Revision set already claimed this floor.')
        pause()
        return
    if not state.next_revision_set:
        print('  No revision set prepared yet.')
        pause()
        return

    for item in state.next_revision_set:
        state.equipment_stash.append(copy.deepcopy(item))

    state.revision_set_claimed = True
    print(f"  Claimed next-revision set: {len(state.next_revision_set)} items added to stash.")
    print('  Sera: "Good. Now we\'re actually planning ahead."')
    pause()



# ─────────────────────────────────────────────────────────
# Simulation mode — summary UI with drill-down
# ─────────────────────────────────────────────────────────

def run_simulation():
    """Run all scripted scenarios from main.py and show summary."""
    from main import run_scenario_1, run_scenario_2, run_scenario_3, run_scenario_4
    ui.clear()
    print(ui.box_top())
    print(ui.box_line("░▒▓█ SIMULATION MODE █▓▒░", "center"))
    print(ui.box_line('Sera: "Show me the math."', "center"))
    print(ui.box_bot())
    print()

    run_scenario_1()
    print("\n" + "─" * 60)
    run_scenario_2()
    print("\n" + "─" * 60)
    run_scenario_3()
    print("\n" + "─" * 60)
    run_scenario_4()

    print()
    print(ui.box_top())
    print(ui.box_line("░▒▓█ SIMULATION COMPLETE █▓▒░", "center"))
    print(ui.box_line('Sera: "Not bad. Not GOOD, but not bad."', "center"))
    print(ui.box_bot())
    pause()


def run_new_game() -> str:
    state = GameState()

    if not choose_starting_weapon(state):
        return "menu"

    for floor_num in range(1, state.max_floors + 1):
        state.floor = floor_num

        enemies = generate_encounter(floor_num, state.all_enemies)

        # Floor intro
        ui.clear()
        print(ui.render_floor_intro(floor_num, enemies, state.interest))
        print(f"  Sera: {sera_quip(FLOOR_INTRO_QUIPS)}")
        pause()

        # Combat
        survived = run_combat(state, enemies)
        if not survived:
            ui.clear()
            print(ui.render_game_over(state.interest, state.floor))
            pause()
            # Show run statistics before returning to main menu
            ui.clear()
            print(ui.render_run_stats(state.run_stats.to_dict(state)))
            pause()
            print(ui.render_post_game(state.run_stats.to_dict(state), won=False))
            post_game_choice = get_choice("  > ", ["1", "2"])
            return "play_again" if post_game_choice == "1" else "menu"

        state.floors_cleared = floor_num

        # Loot
        loot_phase(state)
        state.healing_flasks = min(state.healing_flasks + 1, 3)
        state.next_revision_set = generate_revision_set(state.all_equipment, floor_num + 1)
        state.revision_set_claimed = False

        # Between floors (except after final)
        if floor_num < state.max_floors:
            if not between_floors(state):
                print('  Sera: "Fine. I was getting bored anyway."')
                pause()
                return "menu"


    # Post-game screen with play again option
    ui.clear()
    print(ui.render_victory(state.max_floors, state.interest))
    pause()
    # Show run statistics
    ui.clear()
    print(ui.render_run_stats(state.run_stats.to_dict(state)))
    pause()
    ui.clear()
    print(ui.render_post_game(state.run_stats.to_dict(state), won=True))
    post_game_choice = get_choice("  > ", ["1", "2"])
    return "play_again" if post_game_choice == "1" else "menu"


def main():
    while True:
        choice = title_screen()
        if choice == "quit":
            print("  Sera didn't even show up.")
            return
        if choice == "simulation":
            run_simulation()
            continue

        # choice == "new_game" (or play_again loop)
        result = run_new_game()
        while result == "play_again":
            result = run_new_game()
        if result == "quit":
            return
        # result == "menu" → loop back to title


if __name__ == "__main__":
    main()
