#!/usr/bin/env python3
"""Batch simulation runner for 20 full game sessions with analytics output."""

from __future__ import annotations

import copy
import json
import random
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from play import GameState
from sera.combat import resolve_combat
from sera.crafting import apply_material, upgrade_weapon
from sera.encounters import generate_encounter, generate_loot_material, generate_loot_shards, generate_loot_weapon

GAMES_TO_RUN = 20
BASE_SEED = 90210
REPORT_DIR = Path("reports")
JSON_PATH = REPORT_DIR / "twenty_game_analytics.json"
MD_PATH = REPORT_DIR / "twenty_game_analytics.md"

_DAMAGE_RE = re.compile(r"\b(\d+) damage dealt!")


@dataclass
class FloorRecord:
    floor: int
    weapon: str
    turns_taken: int
    enemies_killed: int
    patience_after_floor: int
    immune_events: int
    misses: int
    dodges: int
    total_damage: int


@dataclass
class GameRecord:
    game: int
    seed: int
    start_weapon: str
    final_weapon: str
    floors_cleared: int
    victory: bool
    game_over: bool
    ending_patience: int
    turns_taken: int
    enemies_killed: int
    immune_events: int
    misses: int
    dodges: int
    total_damage: int
    materials_found: int
    materials_used: int
    upgrades_applied: int
    shard_spent: int
    floor_records: list[FloorRecord]
    break_reason: str


def _choose_starting_weapon(state: GameState) -> None:
    heavy = [w for w in state.all_weapons if w.base_damage >= 3]
    light = [w for w in state.all_weapons if w.base_damage < 3]
    if heavy and light:
        options = [random.choice(heavy)] + random.sample(light, min(2, len(light)))
        random.shuffle(options)
    else:
        options = random.sample(state.all_weapons, min(3, len(state.all_weapons)))
    picked = copy.deepcopy(options[0])
    state.weapons.append(picked)
    state.equipped_idx = 0


def _weapon_score(weapon) -> float:
    affixes = sum(1 for a in [weapon.prefix, weapon.suffix, weapon.set_bonus] if a)
    return weapon.effective_base_damage * 10 + len(weapon.all_tags) + affixes * 1.5


def _parse_combat_log(log: list[str]) -> tuple[int, int, int, int]:
    immune_events = sum(1 for line in log if "IMMUNE." in line)
    misses = sum(1 for line in log if "MISS." in line)
    dodges = sum(1 for line in log if "dodges." in line)
    total_damage = 0
    for line in log:
        m = _DAMAGE_RE.search(line)
        if m:
            total_damage += int(m.group(1))
    return immune_events, misses, dodges, total_damage


def run_game(game_index: int, seed: int) -> GameRecord:
    random.seed(seed)
    state = GameState()
    _choose_starting_weapon(state)

    floors_cleared = 0
    turns_taken = 0
    enemies_killed = 0
    immune_events = 0
    misses = 0
    dodges = 0
    total_damage = 0
    materials_found = 0
    materials_used = 0
    upgrades_applied = 0
    shard_spent = 0
    floor_records: list[FloorRecord] = []
    break_reason = "Victory"

    for floor in range(1, state.max_floors + 1):
        state.floor = floor
        encounter = generate_encounter(floor, state.all_enemies)
        result = resolve_combat(state.equipped_weapon, encounter, state.interest, max_turns=35)
        imm, miss, dodge, dmg = _parse_combat_log(result.log)

        floors_cleared += 1 if not result.game_over else 0
        turns_taken += result.turns_taken
        enemies_killed += result.enemies_killed
        immune_events += imm
        misses += miss
        dodges += dodge
        total_damage += dmg

        floor_records.append(FloorRecord(
            floor=floor,
            weapon=state.equipped_weapon.display_name,
            turns_taken=result.turns_taken,
            enemies_killed=result.enemies_killed,
            patience_after_floor=result.patience_remaining,
            immune_events=imm,
            misses=miss,
            dodges=dodge,
            total_damage=dmg,
        ))

        if result.game_over:
            if imm > 0:
                break_reason = "Game over after repeated immunity lockout"
            else:
                break_reason = "Game over from patience drain"
            break

        # Loot/crafting loop for surviving floor.
        new_weapon = generate_loot_weapon(floor, state.all_weapons, state.all_affixes)
        if _weapon_score(new_weapon) > _weapon_score(state.equipped_weapon):
            state.weapons.append(new_weapon)
            state.equipped_idx = len(state.weapons) - 1

        material = generate_loot_material()
        if material is not None:
            materials_found += 1
            if random.random() < 0.7:
                apply_material(state.equipped_weapon, material)
                materials_used += 1

        shards = generate_loot_shards(floor)
        state.upgrade_shards += shards
        log, spent = upgrade_weapon(state.equipped_weapon, state.upgrade_shards)
        if spent > 0 and any("UPGRADE" in line for line in log):
            state.upgrade_shards -= spent
            shard_spent += spent
            upgrades_applied += 1

    victory = floors_cleared >= state.max_floors and not state.interest.game_over
    return GameRecord(
        game=game_index,
        seed=seed,
        start_weapon=state.weapons[0].display_name if state.weapons else "None",
        final_weapon=state.equipped_weapon.display_name,
        floors_cleared=floors_cleared,
        victory=victory,
        game_over=state.interest.game_over,
        ending_patience=state.interest.current_patience,
        turns_taken=turns_taken,
        enemies_killed=enemies_killed,
        immune_events=immune_events,
        misses=misses,
        dodges=dodges,
        total_damage=total_damage,
        materials_found=materials_found,
        materials_used=materials_used,
        upgrades_applied=upgrades_applied,
        shard_spent=shard_spent,
        floor_records=floor_records,
        break_reason=break_reason,
    )


def summarize(records: list[GameRecord]) -> dict:
    victories = [r for r in records if r.victory]
    losses = [r for r in records if not r.victory]
    return {
        "games": len(records),
        "victories": len(victories),
        "losses": len(losses),
        "avg_floors_cleared": round(sum(r.floors_cleared for r in records) / len(records), 2),
        "avg_turns": round(sum(r.turns_taken for r in records) / len(records), 2),
        "avg_damage": round(sum(r.total_damage for r in records) / len(records), 2),
        "total_immune_events": sum(r.immune_events for r in records),
        "total_misses": sum(r.misses for r in records),
        "total_dodges": sum(r.dodges for r in records),
        "break_reasons": {
            "immunity_lockout": sum(1 for r in losses if "immunity" in r.break_reason.lower()),
            "patience_drain": sum(1 for r in losses if "patience" in r.break_reason.lower()),
        },
    }


def write_markdown(records: list[GameRecord], aggregate: dict) -> None:
    lines = [
        "# Twenty-Game Analytics Report",
        "",
        f"- Runs: **{aggregate['games']}**",
        f"- Victories: **{aggregate['victories']}**",
        f"- Losses: **{aggregate['losses']}**",
        f"- Avg floors cleared: **{aggregate['avg_floors_cleared']}**",
        f"- Avg turns (cumulative run count): **{aggregate['avg_turns']}**",
        f"- Avg damage dealt: **{aggregate['avg_damage']}**",
        f"- Total immunity events: **{aggregate['total_immune_events']}**",
        f"- Total misses: **{aggregate['total_misses']}**",
        f"- Total dodges: **{aggregate['total_dodges']}**",
        "",
        "## Break Analysis",
        "",
        f"- Losses caused by immunity lockout: **{aggregate['break_reasons']['immunity_lockout']}**",
        f"- Losses caused by patience drain (non-immunity): **{aggregate['break_reasons']['patience_drain']}**",
        "- Dominant failure mode: progression can stall when a run reaches tag-gated enemies without matching weapon tags.",
        "",
        "## Per-Run Summary",
        "",
        "| Game | Seed | Start Weapon | Final Weapon | Floors | Victory | Patience | Immune | Miss | Dodge | Damage | Break Reason |",
        "|---:|---:|---|---|---:|:---:|---:|---:|---:|---:|---:|---|",
    ]

    for r in records:
        lines.append(
            f"| {r.game} | {r.seed} | {r.start_weapon} | {r.final_weapon} | {r.floors_cleared} | {'Y' if r.victory else 'N'} | {r.ending_patience} | {r.immune_events} | {r.misses} | {r.dodges} | {r.total_damage} | {r.break_reason} |"
        )

    lines.extend([
        "",
        "## Recommendations",
        "",
        "1. Add a guaranteed tag-repair action before floor 4+ (crafting fallback or mercy tag infusion).",
        "2. Weight loot generation toward missing vulnerability tags when immunity events are detected in-combat.",
        "3. Consider a soft-fail rule: first immune hit in an encounter grants a one-time material drop for counterplay.",
    ])

    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    records = [run_game(idx, BASE_SEED + idx) for idx in range(1, GAMES_TO_RUN + 1)]
    aggregate = summarize(records)

    JSON_PATH.write_text(
        json.dumps(
            {
                "aggregate": aggregate,
                "games": [asdict(r) for r in records],
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    write_markdown(records, aggregate)

    print(json.dumps(aggregate, indent=2))
    print(f"Wrote {JSON_PATH} and {MD_PATH}")


if __name__ == "__main__":
    main()
