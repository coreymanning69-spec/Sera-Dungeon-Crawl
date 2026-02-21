#!/usr/bin/env python3
"""SERA: ENDLESS ENGAGEMENT — Randomized Simulation Runner."""

from __future__ import annotations
import copy
import random

from sera import GAME_REVISION, GAME_TAGLINE, GAME_TITLE
from sera.loader import load_weapons, load_enemies
from sera.interest import InterestManager
from sera.combat import resolve_combat


def banner(text: str) -> str:
    width = 60
    return f"\n{'#' * width}\n#  {text.center(width - 6)}  #\n{'#' * width}"


def run_randomized_scenario(idx: int, verbose: bool = True) -> dict:
    """Run a randomized combat scenario and return structured results."""
    all_weapons = load_weapons()
    all_enemies = load_enemies()

    weapon = copy.deepcopy(random.choice(all_weapons))
    enemy_count = random.randint(1, min(3, len(all_enemies)))
    enemies = [copy.deepcopy(e) for e in random.sample(all_enemies, k=enemy_count)]

    starting_patience = random.randint(65, 100)
    max_turns = random.randint(3, 8)
    interest = InterestManager(current_patience=starting_patience)

    result = resolve_combat(weapon, enemies, interest, max_turns=max_turns)
    payload = {
        "name": f"Random Scenario {idx}",
        "kills": result.enemies_killed,
        "patience": result.patience_remaining,
        "max_patience": interest.max_patience,
        "turns": result.turns_taken,
        "game_over": result.game_over,
        "log": result.log,
        "weapon": weapon.display_name,
        "enemies": [e.name for e in enemies],
        "max_turns": max_turns,
    }

    if verbose:
        print(banner(payload["name"]))
        print(f'  "Randomized pressure test. Adapt or disappoint me."')
        print(f"  Weapon: {payload['weapon']}")
        print(f"  Enemies: {', '.join(payload['enemies'])}")
        print(f"  Start Patience: {starting_patience}  |  Max Turns: {max_turns}")
        for line in result.log:
            print(line)
        print(
            f"\n  Result: {payload['kills']} kills, "
            f"{payload['patience']}/{payload['max_patience']} Patience, "
            f"{'GAME OVER' if payload['game_over'] else 'Sera continues.'}"
        )
    return payload


def run_randomized_simulation(scenarios: int = 5, verbose: bool = True) -> list[dict]:
    """Run a set of randomized scenarios."""
    results: list[dict] = []
    for i in range(1, scenarios + 1):
        results.append(run_randomized_scenario(i, verbose=verbose))
    return results



def run_scenario_1(verbose: bool = True) -> dict:
    return run_randomized_scenario(1, verbose=verbose)


def run_scenario_2(verbose: bool = True) -> dict:
    return run_randomized_scenario(2, verbose=verbose)


def run_scenario_3(verbose: bool = True) -> dict:
    return run_randomized_scenario(3, verbose=verbose)



def main():
    print(banner(GAME_TITLE))
    print('  "I am a Goddess. Entertain me or I leave."')
    print(f"  {GAME_TAGLINE}")
    print(f"  Revision {GAME_REVISION}")
    print(f"  {'─' * 40}")
    print("  Random Simulation Loop: each scenario rolls a weapon, enemies, and pacing.")
    print("  Legacy scripted scenarios were preserved in legacy_simulation.py.")

    results = run_randomized_simulation(scenarios=5, verbose=True)

    print(banner("END OF RANDOMIZED SIMULATION"))
    clears = sum(1 for r in results if not r["game_over"])
    print(f"  Scenarios run: {len(results)}")
    print(f"  Cleared without game over: {clears}")
    print('  Sera: "Not bad. Not GOOD, but not bad."')


if __name__ == "__main__":
    main()
