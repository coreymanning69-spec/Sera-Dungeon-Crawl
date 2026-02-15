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


def pause(msg: str = "  [Press Enter to continue]"):
    ui.get_input(msg)


# ─────────────────────────────────────────────────────────
# Title screen
# ─────────────────────────────────────────────────────────

def title_screen() -> bool:
    ui.clear()
    print(ui.render_title_screen())
    choice = get_choice("> ", ["1", "2"])
    return choice == "1"


# ─────────────────────────────────────────────────────────
# Weapon selection at game start
# ─────────────────────────────────────────────────────────

def choose_starting_weapon(state: GameState):
    ui.clear()
    # Offer 3 random weapons
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

    while True:
        alive = [e for e in enemies if e.current_hp > 0]
        if not alive:
            ui.clear()
            print(ui.box_top())
            print(ui.box_line("ROOM CLEARED", "center"))
            print(ui.box_line('"That was almost interesting."', "center"))
            print(ui.box_bot())
            pause()
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
        print(ui.render_combat_hud(combat_turn, weapon, enemies, interest))

        quip = interest._time_quip()
        print(f'  Sera: "{quip}"')
        print(f"  [-1 Patience] Time ticks.")
        print()

        # Get player action
        valid_actions = [str(i+1) for i in range(len(alive))] + ["i", "w"]
        action = None
        while action is None:
            choice = get_choice("  Your move > ", valid_actions)
            if choice == "quit":
                return False
            if choice == "i":
                # Inspect
                if len(alive) == 1:
                    inspect_idx = 0
                else:
                    print(f"  Which enemy? [1-{len(alive)}]")
                    ic = get_choice("  > ", [str(i+1) for i in range(len(alive))])
                    if ic == "quit":
                        return False
                    inspect_idx = int(ic) - 1
                ui.clear()
                print(ui.render_inspect(alive[inspect_idx]))
                pause()
                ui.clear()
                print(ui.render_combat_hud(combat_turn, weapon, enemies, interest))
                continue
            if choice == "w":
                ui.clear()
                print(ui.render_weapon_detail(weapon))
                pause()
                ui.clear()
                print(ui.render_combat_hud(combat_turn, weapon, enemies, interest))
                continue
            action = int(choice) - 1

        target = alive[action]

        # --- RESOLVE ATTACK ---
        print()
        if not target.check_permission(weapon.all_tags):
            print(f'  Sera attacks {target.name} with {weapon.display_name}...')
            print(f'  IMMUNE. Wrong tags.')
            print(f'  Sera: "Boring. I can\'t even touch it."')
            ann_log = interest.take_annoyance(5, f"{target.name} is immune")
            for line in ann_log:
                print(f"  {line.strip()}")
        else:
            damage, steps = weapon.calculate_damage(target)
            hp_before = target.current_hp
            actual, dead = target.take_damage(damage)
            armor_absorbed = damage - actual if damage > actual else 0

            print(ui.render_damage_report(steps, target.name, actual, armor_absorbed))

            # Apply statuses from affixes
            for affix in [weapon.prefix, weapon.suffix, weapon.set_bonus]:
                if affix and affix.inflicts_status:
                    effect = StatusEffect[affix.inflicts_status]
                    target.apply_status(effect, affix.status_duration, affix.status_potency)
                    print(f'  Applied {effect.name}!')

            print(f"  {target.name}: {ui.hp_bar(target.current_hp, target.max_hp, 15)}")

            if dead:
                kill_log = interest.register_kill(target.name, damage, hp_before)
                print(ui.render_kill_report(target.name, kill_log))

        pause()

        if interest.game_over:
            return False

        # --- ENEMY PHASE ---
        alive = [e for e in enemies if e.current_hp > 0]
        for enemy in alive:
            if interest.game_over:
                return False

            ability = enemy.choose_action()

            if ability is None:
                if enemy.is_casting and enemy.pending_ability:
                    remaining = enemy.cast_turns_remaining
                    ui.clear()
                    print(ui.box_top())
                    print(ui.box_line(f"{enemy.name} is charging...", "center"))
                    print(ui.box_line(f"{enemy.pending_ability.name} ({remaining} turn{'s' if remaining != 1 else ''} left)", "center"))
                    print(ui.box_line(f'Sera: "Hurry up or I\'m leaving."', "center"))
                    print(ui.box_bot())
                    pause()
                continue

            cost = ANNOYANCE_COST[ability.annoyance]
            flavor = ability.flavor or ANNOYANCE_FLAVOR[ability.annoyance]

            ui.clear()
            print(ui.render_enemy_action(enemy, ability.name, flavor, cost))
            interest.take_annoyance(cost, f"{ability.name}")
            print(f"  Patience: {ui.patience_bar(interest)}")
            pause()

            if interest.game_over:
                return False

        # --- CLEANUP PHASE ---
        for enemy in enemies:
            if enemy.current_hp > 0:
                enemy.tick_statuses()
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

    # Pick up loot
    for kind, idx in choices:
        if kind == "weapon":
            print(f"  [{idx}] Take {weapon_drop.display_name}?  [y/n]")
            c = get_choice("  > ", ["y", "n"])
            if c == "y":
                state.weapons.append(weapon_drop)
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
    Between-floor menu: equip, craft, view inventory, or continue.
    Returns False if player quits.
    """
    while True:
        ui.clear()
        print(ui.render_between_floors(state.floor, state.interest))

        choice = get_choice("> ", ["1", "2", "3", "4", "5"])
        if choice in ("quit", "5"):
            return False

        if choice == "1":
            return True  # next floor

        if choice == "2":
            equip_screen(state)

        if choice == "3":
            craft_screen(state)

        if choice == "4":
            ui.clear()
            print(ui.render_inventory(state.weapons, state.materials, state.equipped_idx))
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

    # Pick weapon
    print("  Apply material to which weapon?")
    valid_w = [str(i+1) for i in range(len(state.weapons))] + ["0"]
    wc = get_choice("  Weapon > ", valid_w)
    if wc in ("0", "quit"):
        return
    w_idx = int(wc) - 1

    # Pick material
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

    ui.clear()
    print(ui.box_top())
    print(ui.box_line("CRAFTING", "center"))
    print(ui.box_divider())
    for line in craft_log:
        print(ui.box_line(line.strip()))
    print(ui.box_bot())
    pause()


# ─────────────────────────────────────────────────────────
# Main game loop
# ─────────────────────────────────────────────────────────

def main():
    if not title_screen():
        print("  Sera didn't even show up.")
        return

    state = GameState()

    if not choose_starting_weapon(state):
        return

    for floor_num in range(1, state.max_floors + 1):
        state.floor = floor_num

        # Generate encounter
        enemies = generate_encounter(floor_num, state.all_enemies)

        # Show floor intro
        ui.clear()
        print(ui.render_floor_intro(floor_num, enemies, state.interest))
        sera_lines = [
            '"Let\'s get this over with."',
            '"This better not be boring."',
            '"I sense... mediocrity."',
            '"Show me something new."',
            '"Last chance to impress me."',
        ]
        print(f"  Sera: {sera_lines[min(floor_num - 1, len(sera_lines) - 1)]}")
        pause()

        # Run combat
        survived = run_combat(state, enemies)
        if not survived:
            ui.clear()
            print(ui.render_game_over(state.interest))
            return

        # Loot
        loot_phase(state)

        # Between floors (except after final floor)
        if floor_num < state.max_floors:
            if not between_floors(state):
                print('  Sera: "Fine. I was getting bored anyway."')
                return

    # Victory
    ui.clear()
    print(ui.render_victory(state.max_floors, state.interest))


if __name__ == "__main__":
    main()
