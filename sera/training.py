"""Training Grounds and combat-lab scenario execution."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from sera.combat import resolve_combat
from sera.encounters import generate_endless_encounter
from sera.enemy import Enemy
from sera.interest import InterestManager
from sera.loot_framework import WeaponPoolManager
from sera.randomization import RunRNG
from sera.tags import EnemyVulnerability
from sera.weapon import Affix, Weapon


TRAINING_FOCUSES = {"mixed", "trash", "elite", "boss", "tag_drill"}
TRAINING_BUILD_RULES = {"random_drop", "fixed_starter", "tag_drill", "legendary_trial"}


@dataclass(frozen=True)
class TrainingScenarioSpec:
    key: str
    label: str
    description: str
    level_start: int = 1
    wave_count: int = 4
    enemy_focus: str = "mixed"
    build_rule: str = "random_drop"
    max_turns: int = 10
    seed: int = 1337
    difficulty: float = 1.0
    reward_gold: int = 12
    auto_only: bool = True

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "level_start": self.level_start,
            "wave_count": self.wave_count,
            "enemy_focus": self.enemy_focus,
            "build_rule": self.build_rule,
            "max_turns": self.max_turns,
            "seed": self.seed,
            "difficulty": self.difficulty,
            "reward_gold": self.reward_gold,
            "auto_only": self.auto_only,
        }


@dataclass
class TrainingWaveResult:
    wave: int
    level: int
    weapon_name: str
    enemy_names: list[str]
    turns: int
    kills: int
    patience: int
    damage: int
    immune_hits: int
    game_over: bool

    def to_dict(self) -> dict:
        return {
            "wave": self.wave,
            "level": self.level,
            "weapon_name": self.weapon_name,
            "enemy_names": list(self.enemy_names),
            "turns": self.turns,
            "kills": self.kills,
            "patience": self.patience,
            "damage": self.damage,
            "immune_hits": self.immune_hits,
            "game_over": self.game_over,
        }


@dataclass
class CombatRunSummary:
    spec: TrainingScenarioSpec
    waves: list[TrainingWaveResult]
    total_turns: int
    total_kills: int
    total_damage: int
    total_immune_hits: int
    patience_remaining: int
    won: bool
    reward_gold: int
    failure_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "spec": self.spec.to_dict(),
            "waves": [wave.to_dict() for wave in self.waves],
            "total_turns": self.total_turns,
            "total_kills": self.total_kills,
            "total_damage": self.total_damage,
            "total_immune_hits": self.total_immune_hits,
            "patience_remaining": self.patience_remaining,
            "won": self.won,
            "reward_gold": self.reward_gold,
            "failure_reason": self.failure_reason,
        }


@dataclass
class TrainingBatchSummary:
    spec: TrainingScenarioSpec
    runs: list[CombatRunSummary] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        if not self.runs:
            return 0.0
        wins = sum(1 for run in self.runs if run.won)
        return wins / len(self.runs)

    @property
    def average_turns(self) -> float:
        if not self.runs:
            return 0.0
        return sum(run.total_turns for run in self.runs) / len(self.runs)

    @property
    def average_damage(self) -> float:
        if not self.runs:
            return 0.0
        return sum(run.total_damage for run in self.runs) / len(self.runs)

    def to_dict(self) -> dict:
        return {
            "spec": self.spec.to_dict(),
            "runs": [run.to_dict() for run in self.runs],
            "win_rate": self.win_rate,
            "average_turns": self.average_turns,
            "average_damage": self.average_damage,
        }


def default_training_presets() -> list[TrainingScenarioSpec]:
    return [
        TrainingScenarioSpec(
            key="sparring_ladder",
            label="Sparring Ladder",
            description="Four mixed waves for quick build checks.",
            level_start=1,
            wave_count=4,
            enemy_focus="mixed",
            build_rule="random_drop",
            max_turns=10,
            reward_gold=14,
        ),
        TrainingScenarioSpec(
            key="tag_doctrine",
            label="Tag Doctrine",
            description="Vulnerability-gated enemies with tag-aware weapons.",
            level_start=2,
            wave_count=5,
            enemy_focus="tag_drill",
            build_rule="tag_drill",
            max_turns=12,
            reward_gold=18,
        ),
        TrainingScenarioSpec(
            key="elite_pressure",
            label="Elite Pressure",
            description="Elite-heavy waves that test patience economy.",
            level_start=4,
            wave_count=5,
            enemy_focus="elite",
            build_rule="random_drop",
            max_turns=12,
            difficulty=1.1,
            reward_gold=24,
        ),
        TrainingScenarioSpec(
            key="boss_rehearsal",
            label="Boss Rehearsal",
            description="Short boss ladder for defense and burst checks.",
            level_start=5,
            wave_count=3,
            enemy_focus="boss",
            build_rule="legendary_trial",
            max_turns=14,
            difficulty=1.15,
            reward_gold=30,
        ),
    ]


def get_training_preset(key: str) -> TrainingScenarioSpec | None:
    for preset in default_training_presets():
        if preset.key == key:
            return preset
    return None


def execute_training_scenario(
    spec: TrainingScenarioSpec,
    all_weapons: list[Weapon],
    all_affixes: list[Affix],
    all_enemies: list[Enemy],
) -> CombatRunSummary:
    rng = RunRNG(spec.seed)
    weapon_manager = WeaponPoolManager(all_weapons, all_affixes, rng)
    wave_results: list[TrainingWaveResult] = []
    total_turns = 0
    total_kills = 0
    total_damage = 0
    total_immune_hits = 0
    failure_reason = ""

    for offset in range(spec.wave_count):
        wave = offset + 1
        level = spec.level_start + offset
        enemies = _build_training_encounter(spec, level, all_enemies, rng)
        weapon = _select_training_weapon(spec, level, enemies, all_weapons, weapon_manager)
        start_hp = sum(max(0, enemy.current_hp) for enemy in enemies)
        interest = InterestManager(current_patience=80, max_patience=80)
        result = resolve_combat(weapon, enemies, interest, max_turns=spec.max_turns)
        end_hp = sum(max(0, enemy.current_hp) for enemy in result.final_enemies)
        damage = max(0, start_hp - end_hp)
        immune_hits = sum(1 for line in result.log if "IMMUNE" in line)

        total_turns += result.turns_taken
        total_kills += result.enemies_killed
        total_damage += damage
        total_immune_hits += immune_hits

        wave_results.append(
            TrainingWaveResult(
                wave=wave,
                level=level,
                weapon_name=weapon.display_name,
                enemy_names=[enemy.name for enemy in enemies],
                turns=result.turns_taken,
                kills=result.enemies_killed,
                patience=result.patience_remaining,
                damage=damage,
                immune_hits=immune_hits,
                game_over=result.game_over,
            )
        )
        if result.game_over:
            failure_reason = "patience_broken"
            break

    won = len(wave_results) == spec.wave_count and not any(wave.game_over for wave in wave_results)
    if not won and not failure_reason:
        failure_reason = "scenario_incomplete"
    reward_gold = spec.reward_gold if won else max(1, spec.reward_gold // 3)
    return CombatRunSummary(
        spec=spec,
        waves=wave_results,
        total_turns=total_turns,
        total_kills=total_kills,
        total_damage=total_damage,
        total_immune_hits=total_immune_hits,
        patience_remaining=wave_results[-1].patience if wave_results else 80,
        won=won,
        reward_gold=reward_gold,
        failure_reason=failure_reason,
    )


def execute_training_batch(
    spec: TrainingScenarioSpec,
    all_weapons: list[Weapon],
    all_affixes: list[Affix],
    all_enemies: list[Enemy],
    *,
    runs: int = 5,
) -> TrainingBatchSummary:
    batch = TrainingBatchSummary(spec=spec)
    for idx in range(max(1, runs)):
        run_spec = TrainingScenarioSpec(
            **{**spec.to_dict(), "seed": spec.seed + idx}
        )
        batch.runs.append(execute_training_scenario(run_spec, all_weapons, all_affixes, all_enemies))
    return batch


def _build_training_encounter(
    spec: TrainingScenarioSpec,
    level: int,
    all_enemies: list[Enemy],
    rng: RunRNG,
) -> list[Enemy]:
    if spec.enemy_focus == "mixed":
        enemies = generate_endless_encounter(level, all_enemies, rng=rng)
    else:
        pool = _enemy_pool_for_focus(spec.enemy_focus, all_enemies)
        count = _enemy_count_for_focus(spec.enemy_focus, level)
        enemies = [copy.deepcopy(rng.choice(pool)) for _ in range(count)] if pool else []

    for enemy in enemies:
        _apply_training_difficulty(enemy, level, spec.difficulty)
    return enemies


def _enemy_pool_for_focus(focus: str, all_enemies: list[Enemy]) -> list[Enemy]:
    if focus in {"trash", "elite", "boss"}:
        pool = [enemy for enemy in all_enemies if enemy.archetype == focus]
    elif focus == "tag_drill":
        pool = [enemy for enemy in all_enemies if enemy.vulnerability != EnemyVulnerability.NONE]
    else:
        pool = list(all_enemies)
    return pool or list(all_enemies)


def _enemy_count_for_focus(focus: str, level: int) -> int:
    if focus == "boss":
        return 1
    if focus == "elite":
        return 1 + min(2, level // 6)
    if focus == "tag_drill":
        return 2 if level < 6 else 3
    return 1 + min(3, level // 3)


def _apply_training_difficulty(enemy: Enemy, level: int, difficulty: float) -> None:
    multiplier = max(0.5, difficulty)
    if multiplier != 1.0:
        enemy.max_hp = max(1, int(round(enemy.max_hp * multiplier)))
        enemy.current_hp = enemy.max_hp
    if level >= 4:
        enemy.armor += max(0, int((level - 2) * max(0.0, difficulty - 0.95) * 0.35))


def _select_training_weapon(
    spec: TrainingScenarioSpec,
    level: int,
    enemies: list[Enemy],
    all_weapons: list[Weapon],
    weapon_manager: WeaponPoolManager,
) -> Weapon:
    if spec.build_rule == "fixed_starter" and all_weapons:
        return copy.deepcopy(all_weapons[0])
    if spec.build_rule == "legendary_trial":
        return weapon_manager.generate_drop(max(level, 8))
    if spec.build_rule == "tag_drill":
        for weapon in all_weapons:
            if any(enemy.check_permission(set(weapon.all_tags)) for enemy in enemies):
                return copy.deepcopy(weapon)
    return weapon_manager.generate_drop(level)
