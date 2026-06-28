from __future__ import annotations

from sera.loader import load_affixes, load_enemies, load_weapons
from sera.training import (
    TrainingScenarioSpec,
    default_training_presets,
    execute_training_batch,
    execute_training_scenario,
)


def test_default_training_presets_are_configured() -> None:
    presets = default_training_presets()

    assert len(presets) >= 4
    assert {preset.key for preset in presets} >= {
        "sparring_ladder",
        "tag_doctrine",
        "elite_pressure",
        "boss_rehearsal",
    }
    assert all(preset.wave_count > 0 for preset in presets)
    assert all(preset.reward_gold > 0 for preset in presets)


def test_training_scenario_returns_structured_summary() -> None:
    spec = TrainingScenarioSpec(
        key="test",
        label="Test Drill",
        description="Small deterministic check.",
        level_start=1,
        wave_count=2,
        enemy_focus="trash",
        build_rule="fixed_starter",
        max_turns=6,
        seed=99,
    )

    summary = execute_training_scenario(spec, load_weapons(), load_affixes(), load_enemies())

    assert summary.spec.key == "test"
    assert 1 <= len(summary.waves) <= 2
    assert summary.total_turns >= 0
    assert summary.reward_gold > 0
    assert summary.to_dict()["spec"]["enemy_focus"] == "trash"


def test_training_batch_varies_seed_and_reports_aggregates() -> None:
    spec = TrainingScenarioSpec(
        key="batch_test",
        label="Batch Test",
        description="Batch deterministic check.",
        wave_count=1,
        enemy_focus="mixed",
        build_rule="random_drop",
        seed=5,
    )

    batch = execute_training_batch(spec, load_weapons(), load_affixes(), load_enemies(), runs=3)

    assert len(batch.runs) == 3
    assert 0.0 <= batch.win_rate <= 1.0
    assert batch.average_turns >= 0
    assert [run.spec.seed for run in batch.runs] == [5, 6, 7]
