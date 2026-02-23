from __future__ import annotations

import copy

from sera.loader import load_affixes, load_enemies, load_weapons
from sera.unique_items import ARTIFACT_NAMES, UNIQUE_ITEM_PROFILES


def test_content_counts_after_overhaul() -> None:
    enemies = load_enemies()
    weapons = load_weapons()

    assert len(enemies) >= 50
    assert len(weapons) >= 54
    assert all(name in UNIQUE_ITEM_PROFILES for name in ARTIFACT_NAMES)


def test_twenty_artifact_affix_combinations_are_valid() -> None:
    weapons = load_weapons()
    affixes = load_affixes()
    prefixes = [a for a in affixes if a.affix_type == "prefix"]
    suffixes = [a for a in affixes if a.affix_type == "suffix"]
    enemy = copy.deepcopy(load_enemies()[0])

    artifact_weapons = [w for w in weapons if w.name in ARTIFACT_NAMES]
    assert len(artifact_weapons) >= 20

    for idx, weapon in enumerate(artifact_weapons[:20]):
        candidate = copy.deepcopy(weapon)
        candidate.prefix = copy.deepcopy(prefixes[idx % len(prefixes)])
        candidate.suffix = copy.deepcopy(suffixes[idx % len(suffixes)])
        dmg, _ = candidate.calculate_damage(enemy, enemy_count=1)
        assert 0 <= dmg <= 30
