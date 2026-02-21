#!/usr/bin/env python3
"""
20-Run Simulation Analysis for SERA: ENDLESS ENGAGEMENT

Runs 20 complete games with automated decision-making and collects statistics
to identify patterns in success/failure, difficulty spikes, and build effectiveness.
"""

from __future__ import annotations
import copy
import random
from dataclasses import dataclass
import json

from sera.weapon import Weapon
from sera.enemy import Enemy
from sera.interest import InterestManager
from sera.loader import load_weapons, load_affixes, load_enemies
from sera.encounters import generate_encounter, generate_loot_weapon, generate_loot_material
from sera.combat import resolve_combat
from sera.crafting import CRAFTING_MATERIALS, apply_material
from sera.tags import DamageTag


@dataclass
class RunStats:
    """Stats for a single run."""
    run_num: int
    seed: int
    max_floor_reached: int
    final_patience: int
    total_turns: int
    total_kills: int
    total_damage: int
    weapons_collected: int
    materials_used: int
    crafted_weapons: list[str]
    game_over_reason: str  # "patience" or "victory" or "incomplete"
    floor_times: dict[int, int]  # floor -> turns to clear


def simulate_ai_run(run_num: int, seed: int) -> RunStats:
    """Run a single game with AI decision-making."""
    random.seed(seed)

    stats = RunStats(
        run_num=run_num,
        seed=seed,
        max_floor_reached=0,
        final_patience=100,
        total_turns=0,
        total_kills=0,
        total_damage=0,
        weapons_collected=0,
        materials_used=0,
        crafted_weapons=[],
        game_over_reason="incomplete",
        floor_times={}
    )

    # Load game data
    all_weapons = load_weapons()
    all_affixes = load_affixes()
    all_enemies = load_enemies()

    # Start game with random weapon choice
    starting_weapons = random.sample(all_weapons, min(3, len(all_weapons)))
    equipped_weapon = copy.deepcopy(random.choice(starting_weapons))
    weapons = [equipped_weapon]
    materials = []

    interest = InterestManager()

    # Run through 5 floors
    for floor_num in range(1, 6):
        stats.max_floor_reached = floor_num

        # Generate encounter
        enemies = generate_encounter(floor_num, all_enemies)

        # Combat
        turn_before = interest.turn_number
        result = resolve_combat(equipped_weapon, enemies, interest, max_turns=30)
        turns_this_floor = interest.turn_number - turn_before
        stats.floor_times[floor_num] = turns_this_floor
        stats.total_turns = interest.turn_number
        stats.total_kills += result.enemies_killed

        # Track damage from log (rough estimate)
        for line in result.log:
            if "damage" in line.lower() and any(c.isdigit() for c in line):
                try:
                    # Extract damage numbers from combat log
                    import re
                    matches = re.findall(r'(\d+)\s*damage', line)
                    if matches:
                        stats.total_damage += sum(int(m) for m in matches)
                except:
                    pass

        stats.final_patience = interest.current_patience

        if result.game_over:
            stats.game_over_reason = "patience"
            break

        # Loot phase - AI picks weapons
        if random.random() < 0.6:  # 60% chance to take found weapon
            weapon_drop = generate_loot_weapon(floor_num, all_weapons, all_affixes)
            if weapon_drop:
                weapons.append(weapon_drop)
                stats.weapons_collected += 1

        # Loot phase - AI picks materials
        if random.random() < 0.5:  # 50% chance to take found material
            material_drop = generate_loot_material()
            if material_drop:
                materials.append(material_drop)

        # Between-floor actions (AI decision)
        # - Swap weapon if available (sometimes)
        if len(weapons) > 1 and random.random() < 0.4:
            # Look for weapon with vulnerability coverage
            floor_enemies = generate_encounter(floor_num, all_enemies)
            required_tags = set()
            for e in floor_enemies:
                if hasattr(e, 'vulnerability') and e.vulnerability:
                    required_tags.add(e.vulnerability.name)

            # Try to find better weapon
            for w in weapons:
                if any(tag.name in str(required_tags) for tag in w.all_tags):
                    equipped_weapon = w
                    break

        # Apply materials sometimes (AI decides)
        if materials and random.random() < 0.3:
            material = random.choice(materials)
            apply_material(equipped_weapon, material)
            materials.remove(material)
            stats.materials_used += 1
            stats.crafted_weapons.append(equipped_weapon.name)

    if stats.max_floor_reached == 5 and stats.final_patience > 0:
        stats.game_over_reason = "victory"

    return stats


def print_summary(all_stats: list[RunStats]):
    """Print analysis of 20 runs."""
    print("\n" + "=" * 70)
    print("20-RUN SIMULATION ANALYSIS".center(70))
    print("=" * 70 + "\n")

    # Victory stats
    victories = [s for s in all_stats if s.game_over_reason == "victory"]
    patience_losses = [s for s in all_stats if s.game_over_reason == "patience"]

    print(f"OUTCOMES:")
    print(f"  Victories: {len(victories)}/20 ({100*len(victories)//20}%)")
    print(f"  Patience Losses: {len(patience_losses)}/20 ({100*len(patience_losses)//20}%)")
    print(f"  Avg floor reached: {sum(s.max_floor_reached for s in all_stats) / len(all_stats):.1f}")
    print()

    # Floor-by-floor analysis
    print("FLOOR ANALYSIS:")
    for floor in range(1, 6):
        floor_stats = [s for s in all_stats if s.max_floor_reached >= floor]
        if not floor_stats:
            continue

        survived = len([s for s in floor_stats if s.max_floor_reached > floor or s.game_over_reason == "victory"])
        avg_turns = sum(s.floor_times.get(floor, 0) for s in floor_stats) / len(floor_stats)
        avg_patience_start = 100 - (sum(s.floor_times.get(i, 0) for i in range(1, floor)) for s in floor_stats).__next__() if floor > 1 else 100

        print(f"  Floor {floor}: {len(floor_stats)} reached | "
              f"{survived}/{len(floor_stats)} survived | "
              f"Avg {avg_turns:.1f} turns")
    print()

    # Kill and damage stats
    print("COMBAT METRICS:")
    avg_kills = sum(s.total_kills for s in all_stats) / len(all_stats)
    avg_damage = sum(s.total_damage for s in all_stats) / len(all_stats)
    avg_turns = sum(s.total_turns for s in all_stats) / len(all_stats)

    print(f"  Avg kills per run: {avg_kills:.1f}")
    print(f"  Avg damage per run: {avg_damage:.1f}")
    print(f"  Avg turns per run: {avg_turns:.1f}")
    print(f"  Avg kills per turn: {avg_kills/avg_turns:.2f}")
    print()

    # Loot stats
    print("LOOT & CRAFTING:")
    avg_weapons_found = sum(s.weapons_collected for s in all_stats) / len(all_stats)
    avg_materials_used = sum(s.materials_used for s in all_stats) / len(all_stats)

    print(f"  Avg weapons found: {avg_weapons_found:.1f}")
    print(f"  Avg materials used: {avg_materials_used:.1f}")

    craft_count = sum(1 for s in all_stats for _ in s.crafted_weapons)
    print(f"  Total crafting events: {craft_count}")
    print()

    # Patience analysis
    print("PATIENCE ANALYSIS:")
    victory_patience = [s.final_patience for s in victories]
    if victory_patience:
        print(f"  Avg patience at victory: {sum(victory_patience)/len(victory_patience):.0f}")
        print(f"  Min/Max: {min(victory_patience)}/{max(victory_patience)}")

    loss_patience = [s.final_patience for s in patience_losses]
    if loss_patience:
        print(f"  Avg patience at loss: {sum(loss_patience)/len(loss_patience):.0f}")
    print()

    # Difficulty spikes
    print("FLOOR DIFFICULTY (wins only):")
    for floor in range(1, 6):
        floor_wins = [s for s in victories if s.floor_times.get(floor, 0) > 0]
        if floor_wins:
            avg_turns = sum(s.floor_times.get(floor, 0) for s in floor_wins) / len(floor_wins)
            print(f"  Floor {floor}: {avg_turns:.1f} avg turns")
    print()

    # Per-run details
    print("PER-RUN SUMMARY:")
    print(f"{'Run':<4} {'Result':<8} {'Floor':<6} {'Turns':<6} {'Kills':<6} {'Patience':<8}")
    print("─" * 50)
    for s in all_stats:
        result_str = "VICTORY" if s.game_over_reason == "victory" else ("PATIENCE" if s.game_over_reason == "patience" else "STOP")
        print(f"{s.run_num:<4} {result_str:<8} {s.max_floor_reached:<6} {s.total_turns:<6} {s.total_kills:<6} {s.final_patience:<8}")

    print("\n" + "=" * 70)


def main():
    print("SERA: ENDLESS ENGAGEMENT — 20-Run Analysis")
    print("Running 20 full games with AI decision-making...\n")

    all_stats = []
    base_seed = random.randint(1, 1_000_000)

    for run_num in range(1, 21):
        seed = base_seed + run_num
        stats = simulate_ai_run(run_num, seed)
        all_stats.append(stats)

        status = "✓ VICTORY" if stats.game_over_reason == "victory" else "✗ PATIENCE"
        print(f"Run {run_num:2d}: {status:12} Floor {stats.max_floor_reached} | "
              f"{stats.total_turns} turns | {stats.total_kills} kills | "
              f"{stats.final_patience} patience")

    # Print analysis
    print_summary(all_stats)

    # Save detailed data
    output_data = {
        "metadata": {
            "total_runs": 20,
            "base_seed": base_seed,
        },
        "runs": [
            {
                "run_num": s.run_num,
                "seed": s.seed,
                "max_floor_reached": s.max_floor_reached,
                "final_patience": s.final_patience,
                "total_turns": s.total_turns,
                "total_kills": s.total_kills,
                "total_damage": s.total_damage,
                "weapons_collected": s.weapons_collected,
                "materials_used": s.materials_used,
                "game_over_reason": s.game_over_reason,
            }
            for s in all_stats
        ]
    }

    with open("simulation_results.json", "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nDetailed results saved to simulation_results.json")


if __name__ == "__main__":
    main()
