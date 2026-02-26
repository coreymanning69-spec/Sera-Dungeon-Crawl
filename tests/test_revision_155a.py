from __future__ import annotations

from pathlib import Path

from sera.analytics import AnalyticsTracker, export_analytics, load_analytics_index
from sera.enemy import Enemy
from sera.tags import DamageTag, EnemyVulnerability


def test_enemy_missing_tag_hint() -> None:
    enemy = Enemy(
        name="Gatekeeper",
        max_hp=10,
        archetype="elite",
        vulnerability=EnemyVulnerability.REQUIRES_DIVINE_OR_ETHEREAL,
    )
    assert enemy.missing_tag_hint() == "DIVINE or ETHEREAL"
    assert not enemy.check_permission({DamageTag.FIRE})
    assert enemy.check_permission({DamageTag.ETHEREAL})


def test_analytics_export_writes_index(tmp_path: Path) -> None:
    tracker = AnalyticsTracker()
    tracker.capture_turn(
        mode="campaign",
        floor_or_wave=1,
        turn=1,
        patience=80,
        total_kills=0,
        total_damage=0,
        source="combat",
        immune_streak=0,
    )
    json_path, csv_path = export_analytics(tracker, output_dir=tmp_path)
    assert json_path.exists()
    assert csv_path.exists()

    index_path = tmp_path / "analytics_index.json"
    exports = load_analytics_index(index_path)
    assert exports
