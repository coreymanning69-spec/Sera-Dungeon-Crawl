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
from sera.enemy import Enemy, AnnoyanceType, ANNOYANCE_COST, ANNOYANCE_FLAVOR
from sera.interest import InterestManager
from sera.status import StatusEffect
from sera.crafting import CraftingMaterial, apply_material
from sera.loader import load_weapons, load_affixes, load_enemies
from sera.encounters import generate_encounter, generate_loot_weapon, generate_loot_material
from sera import ui


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
]

KILL_QUIPS = [
    '"Finally."',
    '"One down. Keep going."',
    '"That was almost satisfying."',
    '"Acceptable."',
    '"You lasted longer than I expected. Low bar."',
]

OVERKILL_QUIPS = [
    '"NOW we\'re talking."',
    '"Excessive? No. Efficient."',
    '"THAT is how you kill something."',
    '"More of that. Less of everything else."',
]

DODGE_QUIPS = [
    '"Stand still, insect."',
    '"Do that again and I\'m leaving."',
    '"Dodging is for things that fear death. You should."',
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
]

LOW_PATIENCE_QUIPS = [
    '"I\'m running out of reasons to stay."',
    '"This is getting tedious."',
    '"Entertain me or I leave. Simple."',
    '"One more disappointment. That\'s all you get."',
]


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

class GameState:
    def __init__(self):
        self.interest = InterestManager()
        self.floor = 0
        self.max_floors = 5
        self.weapons: list[Weapon] = []
        self.materials: list[CraftingMaterial] = []
        self.equipped_idx: int = 0
        self.all_enemies = load_enemies()
        self.all_weapons = load_weapons()
        self.all_affixes = load_affixes()
        self.floors_cleared: int = 0
        self.run_stats = RunStats()

    @property
    def equipped_weapon(self) -> Weapon:
        return self.weapons[self.equipped_idx]


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
    # Guarantee at least one heavy hitter (3 dmg) in the starting options
    heavy = [w for w in state.all_weapons if w.base_damage >= 3]
    light = [w for w in state.all_weapons if w.base_damage < 3]
    if heavy and light:
        options = [random.choice(heavy)] + random.sample(light, min(2, len(light)))
        random.shuffle(options)
    else:
        options = random.sample(state.all_weapons, min(3, len(state.all_weapons)))

    lines = [
        ui.box_top(),
        ui.box_line("CHOOSE YOUR WEAPON", "center"),
        ui.box_divider(),
        ui.box_line('Sera: "Fine. What are we working with?"'),
        ui.box_blank(),
    ]
    for i, w in enumerate(options):
        tag_str = ", ".join(t.name for t in w.all_tags)
        lines.append(ui.box_line(f"  [{i+1}] {w.name} ({w.base_damage} dmg) [{tag_str}]"))
        lines.append(ui.box_line(f'      "{w.flavor}"'))
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
    auto_battle = False

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
        turn_summary: list[str] = ["Time ticks (-1 Patience)"]
        patience_before_turn = interest.current_patience

        if not auto_battle:
            ui.clear()
            print(ui.render_combat_hud(combat_turn, weapon, enemies, interest))

            # Patience-based commentary
            if interest.current_patience <= 20:
                print(f"  Sera: {sera_quip(LOW_PATIENCE_QUIPS)}")
            else:
                print(f'  Sera: "{interest._time_quip()}"')
            print(f"  [-1 Patience] Time ticks.")
            print()

            # Get player action
            valid_actions = [str(i+1) for i in range(len(alive))] + ["i", "w", "a"]
            action = None
            while action is None:
                choice = get_choice("  Your move > ", valid_actions)
                if choice == "quit":
                    return False
                if choice == "i":
                    _do_inspect(alive, combat_turn, weapon, enemies, interest)
                    continue
                if choice == "w":
                    ui.clear()
                    print(ui.render_weapon_detail(weapon))
                    pause()
                    ui.clear()
                    print(ui.render_combat_hud(combat_turn, weapon, enemies, interest))
                    continue
                if choice == "a":
                    auto_battle = True
                    action = 0
                    break
                action = int(choice) - 1
            target = alive[action]
        else:
            target = alive[0]

        # --- RESOLVE ATTACK ---
        print()
        attack_events = _resolve_player_attack(
            weapon,
            target,
            interest,
            state.run_stats,
            verbose=not auto_battle,
        )
        turn_summary.extend(attack_events)
        if not auto_battle:
            pause()

        if interest.game_over:
            return False

        # --- ENEMY PHASE ---
        alive = [e for e in enemies if e.current_hp > 0]
        for enemy in alive:
            if interest.game_over:
                return False
            enemy_event = _resolve_enemy_action(enemy, interest, verbose=not auto_battle)
            if enemy_event:
                turn_summary.append(enemy_event)

            if interest.game_over:
                return False

        # --- DOT PHASE ---
        for enemy in enemies:
            if enemy.current_hp > 0:
                dot_total, dot_log = enemy.tick_dot_damage()
                if dot_log:
                    kill_name = enemy.name if enemy.current_hp <= 0 else None
                    if not auto_battle:
                        ui.clear()
                        print(ui.render_dot_tick(dot_log, kill_name))
                    turn_summary.extend(line.strip() for line in dot_log)
                    if kill_name:
                        kill_log = interest.register_kill(
                            enemy.name, dot_total, dot_total)
                        if not auto_battle:
                            print(ui.render_kill_report(enemy.name, kill_log))
                        turn_summary.append(f"{enemy.name} dies from DoT")
                        state.run_stats.record_damage(dot_total)
                    if not auto_battle:
                        pause()

        # --- CLEANUP PHASE ---
        for enemy in enemies:
            if enemy.current_hp > 0:
                enemy.tick_statuses()
                enemy.tick_cooldowns()
                healed = enemy.tick_regen()
                if healed > 0:
                    turn_summary.append(f"{enemy.name} regenerates {healed} HP")
                    if not auto_battle:
                        ui.clear()
                        print(ui.box_top())
                        print(ui.box_line(f"{enemy.name} regenerates {healed} HP!", "center"))
                        print(ui.box_line(f"HP: {ui.hp_bar(enemy.current_hp, enemy.max_hp, 15)}", "center"))
                        print(ui.box_line(f'Sera: "Stop healing. It\'s dragging on."', "center"))
                        print(ui.box_bot())
                        pause()

        if auto_battle:
            ui.clear()
            print(ui.render_turn_result(
                combat_turn,
                patience_before_turn,
                interest.current_patience,
                turn_summary,
            ))
            print('  Auto-battle active. Press [Enter] to continue, or type "s" to stop auto.')
            cmd = ui.get_input("  > ").strip().lower()
            if cmd == "s":
                auto_battle = False


def _show_room_clear(interest: InterestManager):
    quips = [
        '"That was almost interesting."',
        '"Is that all? Really?"',
        '"I expected more. I always do."',
        '"Done. What else do you have?"',
    ]
    ui.clear()
    print(ui.box_top())
    print(ui.box_line("ROOM CLEARED", "center"))
    print(ui.box_line(sera_quip(quips), "center"))
    print(ui.box_line(f"Patience: {ui.patience_bar(interest)}", "center"))
    print(ui.box_bot())
    pause()


def _do_inspect(alive, combat_turn, weapon, enemies, interest):
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
    print(ui.render_combat_hud(combat_turn, weapon, enemies, interest))


def _resolve_player_attack(
    weapon: Weapon, target: Enemy, interest: InterestManager,
    run_stats: RunStats,
    verbose: bool = True,
) -> list[str]:
    """Full attack resolution with dodge, permission, interrupt, damage."""
    events: list[str] = []

    # --- Permission Check ---
    if not target.check_permission(weapon.all_tags):
        events.append(f"Attack vs {target.name}: immune")
        if verbose:
            print(f'  Sera attacks {target.name} with {weapon.display_name}...')
            print(f'  IMMUNE. Weapon lacks required tag.')
            print(f'  Sera: {sera_quip(IMMUNE_QUIPS)}')
        ann_log = interest.take_annoyance(5, f"{target.name} is immune")
        if verbose:
            for line in ann_log:
                print(f"  {line.strip()}")
        return events

    # --- Dodge Roll ---
    if target.try_dodge():
        events.append(f"{target.name} dodges")
        if verbose:
            ui.clear()
            print(ui.render_dodge(target.name))
        interest._drain(2, "Dodge")
        return events

    # --- Interrupt Check (hitting a casting enemy cancels their charge) ---
    interrupted = target.interrupt_cast()
    if interrupted:
        events.append(f"Interrupted {target.name} ({interrupted})")
        if verbose:
            ui.clear()
            print(ui.render_interrupt(target.name, interrupted))
        interest._restore(3)
        if verbose:
            print(f"  Sera: {sera_quip(INTERRUPT_QUIPS)}")
            pause()

    # --- Damage Calculation ---
    damage, steps = weapon.calculate_damage(target)
    hp_before = target.current_hp
    actual, dead = target.take_damage(damage)
    armor_absorbed = damage - actual if damage > actual else 0

    run_stats.record_damage(actual)

    events.append(f"Hit {target.name} for {actual}")
    if verbose:
        print(ui.render_damage_report(steps, target.name, actual, armor_absorbed))

    # Attack quip
    if not dead and verbose:
        print(f"  Sera: {sera_quip(ATTACK_QUIPS)}")

    # Apply statuses from affixes
    for affix in [weapon.prefix, weapon.suffix, weapon.set_bonus]:
        if affix and affix.inflicts_status:
            effect = StatusEffect[affix.inflicts_status]
            target.apply_status(effect, affix.status_duration, affix.status_potency)
            events.append(f"Applied {effect.name}")
            if verbose:
                print(f'  Applied {effect.name}!')

    if verbose:
        print(f"  {target.name}: {ui.hp_bar(target.current_hp, target.max_hp, 15)}")

    # --- Kill ---
    if dead:
        kill_log = interest.register_kill(target.name, damage, hp_before)
        events.append(f"Killed {target.name}")
        if verbose:
            print()
            print(f"  Sera: {sera_quip(KILL_QUIPS)}")
        # Check for overkill
        excess = max(0, damage - hp_before)
        if excess > 0:
            events.append(f"Overkill +{excess}")
            if verbose:
                print(f"  Sera: {sera_quip(OVERKILL_QUIPS)}")
            run_stats.record_overkill(excess)
        if verbose:
            print(ui.render_kill_report(target.name, kill_log))

    return events


def _resolve_enemy_action(enemy: Enemy, interest: InterestManager, verbose: bool = True) -> str:
    """Resolve one enemy's turn."""
    ability = enemy.choose_action()

    if ability is None:
        if enemy.is_casting and enemy.pending_ability:
            remaining = enemy.cast_turns_remaining
            if verbose:
                ui.clear()
                print(ui.box_top())
                print(ui.box_line(f"{enemy.name} is charging...", "center"))
                print(ui.box_line(
                    f"{enemy.pending_ability.name} "
                    f"({remaining} turn{'s' if remaining != 1 else ''} left)",
                    "center"))
                print(ui.box_line(f'Sera: "Hurry up or I\'m leaving."', "center"))
                print(ui.box_bot())
                pause()
            return f"{enemy.name} charges {enemy.pending_ability.name}"
        return ""

    cost = ANNOYANCE_COST[ability.annoyance]
    flavor = ability.flavor or ANNOYANCE_FLAVOR[ability.annoyance]

    if verbose:
        ui.clear()
        print(ui.render_enemy_action(enemy, ability.name, flavor, cost))
    interest.take_annoyance(cost, f"{ability.name}")
    if verbose:
        print(f"  Patience: {ui.patience_bar(interest)}")
        pause()
    return f"{enemy.name} uses {ability.name} (-{cost} Patience)"


# ─────────────────────────────────────────────────────────
# Loot phase
# ─────────────────────────────────────────────────────────

def loot_phase(state: GameState):
    """Offer loot after clearing a room."""
    weapon_drop = generate_loot_weapon(state.floor, state.all_weapons, state.all_affixes)
    material_drop = generate_loot_material()

    ui.clear()
    screen, choices = ui.render_loot_screen(weapon_drop, material_drop, state.interest)
    print(screen)

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
    Between-floor menu: equip, craft, view inventory, stats, or continue.
    Returns False if player quits.
    """
    while True:
        ui.clear()
        print(ui.render_between_floors(state.floor, state.interest))

        choice = get_choice("> ", ["1", "2", "3", "4", "5", "6"])
        if choice in ("quit", "6"):
            return False

        if choice == "1":
            return True

        if choice == "2":
            equip_screen(state)

        if choice == "3":
            craft_screen(state)

        if choice == "4":
            ui.clear()
            print(ui.render_inventory(state.weapons, state.materials, state.equipped_idx))
            pause()

        if choice == "5":
            ui.clear()
            print(ui.render_run_stats(state.run_stats.to_dict(state)))
            pause()


def equip_screen(state: GameState):
    if len(state.weapons) < 2:
        print('  Only one weapon. "It\'s not like I have options."')
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


def craft_screen(state: GameState):
    if not state.materials:
        print('  No materials. "Find me something to work with."')
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
    print(ui.box_line("CRAFTING", "center"))
    print(ui.box_divider())
    for line in craft_log:
        print(ui.box_line(line.strip()))
    print(ui.box_bot())
    pause()


# ─────────────────────────────────────────────────────────
# Simulation mode — summary UI with drill-down
# ─────────────────────────────────────────────────────────

def run_simulation():
    """Run the scripted scenarios and show a summary table."""
    from main import run_scenario_1, run_scenario_2, run_scenario_3, run_scenario_4

    ui.clear()
    print(ui.box_top())
    print(ui.box_line("Running simulations...", "center"))
    print(ui.box_bot())

    results = [
        run_scenario_1(verbose=False),
        run_scenario_2(verbose=False),
        run_scenario_3(verbose=False),
        run_scenario_4(verbose=False),
    ]

    while True:
        ui.clear()
        print(ui.render_sim_summary(results))

        valid = [str(i+1) for i in range(len(results))] + ["0"]
        choice = get_choice("> ", valid)

        if choice in ("0", "quit"):
            return

        idx = int(choice) - 1
        ui.clear()
        print(ui.render_sim_detail(results[idx]))
        pause("  [Press Enter to return]")


# ─────────────────────────────────────────────────────────
# Main game loop — with play-again support
# ─────────────────────────────────────────────────────────

def run_new_game() -> str:
    """
    Run the full interactive game.
    Returns 'play_again', 'menu', or 'quit'.
    """
    state = GameState()

    if not choose_starting_weapon(state):
        return "menu"

    won = False
    for floor_num in range(1, state.max_floors + 1):
        state.floor = floor_num

        enemies = generate_encounter(floor_num, state.all_enemies)

        # Floor intro
        ui.clear()
        print(ui.render_floor_intro(floor_num, enemies, state.interest))
        sera_lines = [
            '"Let\'s get this over with."',
            '"This better not be boring."',
            '"I sense... mediocrity ahead."',
            '"Show me something new."',
            '"Last chance. Impress me."',
        ]
        print(f"  Sera: {sera_lines[min(floor_num - 1, len(sera_lines) - 1)]}")
        pause()

        # Combat
        survived = run_combat(state, enemies)
        if not survived:
            break

        state.floors_cleared = floor_num

        # Loot
        loot_phase(state)

        # Between floors (except after final)
        if floor_num < state.max_floors:
            if not between_floors(state):
                print('  Sera: "Fine. I was getting bored anyway."')
                pause()
                return "menu"

        if floor_num == state.max_floors:
            won = True

    # Post-game screen with play again option
    ui.clear()
    stats = state.run_stats.to_dict(state)
    print(ui.render_post_game(stats, won))

    choice = get_choice("> ", ["1", "2"])
    if choice == "1":
        return "play_again"
    return "menu"


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
