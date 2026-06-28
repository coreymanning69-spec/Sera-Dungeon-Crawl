from __future__ import annotations

import random

from play import (
    TowerDefenseRunState,
    _build_tower,
    _build_tower_defense_state,
    _recruit_troop,
    _render_defense_lane,
    _simulate_tower_wave,
)
from sera.enemy import Enemy
from sera.meta import MetaProgression, claim_idle_gold
from sera.tags import EnemyVulnerability


def test_idle_gold_claim_uses_level_rate_and_cap() -> None:
    meta = MetaProgression(idle_level=2, last_idle_claim_ts=1_000)

    claimed, elapsed = claim_idle_gold(meta, now_ts=1_000 + (12 * 60 * 60))

    assert elapsed == 8 * 60 * 60
    assert claimed == 96
    assert meta.banked_gold == 96
    assert meta.last_idle_claim_ts == 1_000 + (12 * 60 * 60)


def test_defense_state_uses_meta_ward_and_idle_levels() -> None:
    meta = MetaProgression(ward_level=2, idle_level=3)

    td_state = _build_tower_defense_state(meta)

    assert td_state.max_core_hp == 56
    assert td_state.core_hp == 56
    assert td_state.resources == 7
    assert td_state.troops["guard"] == 4
    assert td_state.troops["ranger"] == 1
    assert td_state.troops["engineer"] == 1
    assert "#" in td_state.last_battlefield


def test_tower_build_spends_essence_and_increases_level() -> None:
    td_state = TowerDefenseRunState(resources=20)

    ok, message = _build_tower(td_state, "frost")

    assert ok
    assert "Frost Sigil" in message
    assert td_state.towers["frost"] == 1
    assert td_state.resources == 12


def test_troop_recruitment_spends_essence_and_renders_sprite() -> None:
    td_state = TowerDefenseRunState(resources=20)

    ok, message = _recruit_troop(td_state, "ranger")
    lane = _render_defense_lane(td_state, [])

    assert ok
    assert "Ranger Team" in message
    assert td_state.troops["ranger"] == 1
    assert "R" in lane


def test_tower_wave_advances_and_awards_resources() -> None:
    td_state = TowerDefenseRunState(resources=0)
    enemies = [
        Enemy(
            name="Test Crawler",
            max_hp=9,
            archetype="trash",
            vulnerability=EnemyVulnerability.NONE,
        )
    ]

    result = _simulate_tower_wave(td_state, random.Random(7), enemies)

    assert result["wave"] == 1
    assert result["incoming"] > 0
    assert result["essence"] > 0
    assert result["gold"] > 0
    assert "battlefield" in result
    assert result["troop_power"] > 0
    assert result["actions"]
    assert td_state.wave == 2
    assert td_state.gold_earned == result["gold"]
