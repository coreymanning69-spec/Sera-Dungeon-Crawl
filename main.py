#!/usr/bin/env python3
"""
SERA: ENDLESS ENGAGEMENT — Combat Simulation Demo

Runs 3 randomized combat scenarios pulled from the JSON data.
No two runs are identical — weapons, enemies, and affixes are chosen at random.

Scenario 1: "First Contact"  — Random encounter, random weapon
Scenario 2: "Wrong Tool"     — Immune gate, permission failure, crafting fix
Scenario 3: "Boss Fight"     — Random boss, matched weapon, all systems active
"""

from __future__ import annotations
import copy
import random

from sera.tags import DamageTag
from sera.loader import load_weapons, load_affixes, load_enemies
from sera.encounters import generate_encounter, generate_loot_weapon
from sera.interest import InterestManager
from sera.combat import resolve_combat
from sera.crafting import CRAFTING_MATERIALS, apply_material


def banner(text: str) -> str:
    width = 60
    return f"\n{'#' * width}\n#  {text.center(width - 6)}  #\n{'#' * width}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VULN_TO_TAG = {
    "REQUIRES_DIVINE": "DIVINE",
    "REQUIRES_ETHEREAL": "ETHEREAL",
    "REQUIRES_SILVER": "SILVER",
    "REQUIRES_HEAVY": "HEAVY",
    "REQUIRES_CORROSIVE": "CORROSIVE",
    "REQUIRES_FIRE": "FIRE",
    "REQUIRES_ARCANE": "ARCANE",
}


def _pick_weapon_with_affixes(all_weapons, all_affixes, floor, tag_name=None):
    """Pick a random weapon, optionally filtered to a tag. Prefer results with affixes."""
    if tag_name:
        pool = [w for w in all_weapons if tag_name in [t.name for t in w.tags]]
        if not pool:
            pool = all_weapons
    else:
        pool = all_weapons

    for _ in range(10):
        weapon = generate_loot_weapon(floor, pool, all_affixes)
        if weapon.prefix or weapon.suffix:
            return weapon
    return generate_loot_weapon(floor, pool, all_affixes)


def _ensure_can_hit(weapon, enemy):
    """If weapon can't hit enemy, craft the required tag onto it. Returns craft log."""
    if enemy.check_permission(weapon.all_tags):
        return []
    tag_name = _VULN_TO_TAG.get(enemy.vulnerability.name)
    if not tag_name:
        return []
    mat = next((m for m in CRAFTING_MATERIALS.values()
                if m.grants_tag and m.grants_tag.name == tag_name), None)
    if mat:
        return apply_material(weapon, copy.deepcopy(mat))
    weapon.add_tag(DamageTag[tag_name])
    return [f"  Added [{tag_name}] directly. As a Goddess can."]


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def run_scenario_1():
    """First Contact: Random encounter with a random affixed weapon."""
    print(banner("SCENARIO 1: FIRST CONTACT"))

    all_weapons = load_weapons()
    all_affixes = load_affixes()
    all_enemies = load_enemies()

    weapon = _pick_weapon_with_affixes(all_weapons, all_affixes, floor=2)
    enemies = generate_encounter(random.choice([1, 2]), all_enemies)
    interest = InterestManager(current_patience=random.randint(75, 90))

    quip = random.choice([
        "Let's see what we're working with.",
        "Small. Pointless. Probably entertaining enough.",
        "They're already dead. They just don't know it.",
    ])
    print(f'\n  Sera: "{quip}"')
    print(f"\n  Weapon:   {weapon}")
    for e in enemies:
        print(f"  Enemy:    {e}")
    print(f"  Patience: {interest.current_patience}")

    result = resolve_combat(weapon, enemies, interest, max_turns=5)
    for line in result.log:
        print(line)

    print(f"\n  Result: {result.enemies_killed} kills, "
          f"{result.patience_remaining} Patience remaining, "
          f"{'GAME OVER' if result.game_over else 'Sera continues.'}")


def run_scenario_2():
    """Wrong Tool: Random gated elite, permission failure demo, then the crafting fix."""
    print(banner("SCENARIO 2: WRONG TOOL"))

    all_weapons = load_weapons()
    all_affixes = load_affixes()
    all_enemies = load_enemies()

    # Pick an elite with a vulnerability gate
    gated = [e for e in all_enemies
             if e.archetype == "elite" and e.vulnerability.name != "NONE"]
    if not gated:
        gated = [e for e in all_enemies if e.vulnerability.name != "NONE"]
    elite_template = random.choice(gated)
    required_tag_name = _VULN_TO_TAG.get(elite_template.vulnerability.name, "DIVINE")

    # Weapon that CANNOT hit this enemy
    wrong_pool = [w for w in all_weapons
                  if required_tag_name not in [t.name for t in w.tags]]
    if not wrong_pool:
        wrong_pool = all_weapons
    wrong_weapon = copy.deepcopy(random.choice(wrong_pool))

    interest = InterestManager(current_patience=70)

    print(f'\n  Sera: "I brought {wrong_weapon.name}. It needs [{required_tag_name}]."')
    print(f'  Sera: "This is YOUR fault."')
    print(f"\n  --- ATTEMPT 1: Wrong weapon ---")
    print(f"  Weapon: {wrong_weapon}")
    print(f"  Enemy:  {copy.deepcopy(elite_template)}")
    print(f"  Requires: [{required_tag_name}]")

    result1 = resolve_combat(wrong_weapon, [copy.deepcopy(elite_template)], interest, max_turns=2)
    for line in result1.log:
        print(line)

    # Craft the fix
    print(banner("CRAFTING FIX"))
    fix_mat = next((m for m in CRAFTING_MATERIALS.values()
                    if m.grants_tag and m.grants_tag.name == required_tag_name), None)
    if fix_mat:
        print(f'  Sera finds a {fix_mat.name}.')
        craft_log = apply_material(wrong_weapon, copy.deepcopy(fix_mat))
        for line in craft_log:
            print(line)
    else:
        wrong_weapon.add_tag(DamageTag[required_tag_name])
        print(f'  Added [{required_tag_name}] directly. As a Goddess can.')

    # Add a random suffix for punch
    suffixes = [a for a in all_affixes if a.affix_type == "suffix"]
    if suffixes and not wrong_weapon.suffix:
        wrong_weapon.suffix = copy.deepcopy(random.choice(suffixes))
        print(f"  Applies suffix: {wrong_weapon.suffix.name}")

    print(f"\n  --- ATTEMPT 2: Corrected weapon ---")
    print(f"  Weapon: {wrong_weapon}")
    print(f"  Tags:   [{', '.join(t.name for t in wrong_weapon.all_tags)}]")

    result2 = resolve_combat(wrong_weapon, [copy.deepcopy(elite_template)], interest, max_turns=4)
    for line in result2.log:
        print(line)


def run_scenario_3():
    """Boss Fight: Random boss, matched weapon, all systems active."""
    print(banner("SCENARIO 3: BOSS FIGHT"))

    all_weapons = load_weapons()
    all_affixes = load_affixes()
    all_enemies = load_enemies()

    bosses = [e for e in all_enemies if e.archetype == "boss"]
    boss_template = random.choice(bosses) if bosses else random.choice(all_enemies)
    boss = copy.deepcopy(boss_template)

    req_tag_name = _VULN_TO_TAG.get(boss.vulnerability.name)
    weapon = _pick_weapon_with_affixes(all_weapons, all_affixes, floor=5, tag_name=req_tag_name)

    # Pre-craft the required tag if weapon still can't hit the boss
    craft_lines = _ensure_can_hit(weapon, boss)

    interest = InterestManager(current_patience=90)

    quip = random.choice([
        "Now THIS is why I came down here.",
        "Finally. Something worth the trip.",
        "Big. Armored. Still going to die.",
    ])
    print(f'\n  Sera: "{quip}"')
    print(f"\n  Weapon: {weapon}")
    print(f"  Boss:   {boss}")
    print(f"  Starting Patience: {interest.current_patience}")

    if craft_lines:
        print(f"\n  (Pre-fight crafting:)")
        for line in craft_lines:
            print(line)

    result = resolve_combat(weapon, [boss], interest, max_turns=5)
    for line in result.log:
        print(line)

    final_boss = result.final_enemies[0]
    print(f"\n  After {result.turns_taken} turns: "
          f"Boss at {final_boss.current_hp}/{final_boss.max_hp} HP")
    print(f"  Patience: {result.patience_remaining}/{interest.max_patience}")
    print(f"  {'GAME OVER' if result.game_over else 'The fight continues...'}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print(banner("SERA: ENDLESS ENGAGEMENT"))
    print('  "I am a Goddess. Entertain me or I leave."')
    print("  A Systems-Heavy Roguelike Prototype")
    print(f"  {'─' * 40}")
    print("  Core Loop: Kill aggressively to stay interested.")
    print("  Lose State: Patience hits 0. Sera leaves. Game Over.")
    print("  Scale: 1-30 damage. Build the machine, not the number.")
    print("  (Simulation draws from JSON data — each run differs.)")

    run_scenario_1()
    print("\n" + "─" * 60)
    run_scenario_2()
    print("\n" + "─" * 60)
    run_scenario_3()

    print(banner("END OF SIMULATION"))
    print('  Sera: "Not bad. Not GOOD, but not bad."')
    print('  "Build more. I might stay."')


if __name__ == "__main__":
    main()
