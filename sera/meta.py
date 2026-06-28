"""Meta progression persistence and economy for cross-run upgrades."""

from __future__ import annotations

import json
from pathlib import Path
import time
from dataclasses import dataclass

META_PATH = Path("meta_progression.json")


@dataclass
class MetaProgression:
    banked_gold: int = 0
    patience_level: int = 0
    shard_level: int = 0
    flask_level: int = 0
    armory_level: int = 0
    ward_level: int = 0
    idle_level: int = 0
    last_idle_claim_ts: int = 0

    def starting_weapon_slots(self) -> int:
        return 1 + self.armory_level

    def patience_bonus(self) -> int:
        return self.patience_level * 2

    def starting_shards_bonus(self) -> int:
        return self.shard_level

    def starting_flasks_bonus(self) -> int:
        return self.flask_level

    def ward_core_bonus(self) -> int:
        return self.ward_level * 8

    def idle_gold_per_hour(self) -> int:
        return self.idle_level * 6

    def to_dict(self) -> dict:
        return {
            "banked_gold": self.banked_gold,
            "patience_level": self.patience_level,
            "shard_level": self.shard_level,
            "flask_level": self.flask_level,
            "armory_level": self.armory_level,
            "ward_level": self.ward_level,
            "idle_level": self.idle_level,
            "last_idle_claim_ts": self.last_idle_claim_ts,
        }


META_UPGRADES = {
    "patience": {
        "label": "Ritual of Patience",
        "description": "+2 max Patience at run start",
        "field": "patience_level",
        "max_level": 5,
        "base_cost": 40,
        "cost_step": 25,
    },
    "shards": {
        "label": "Shard Stash",
        "description": "+1 Upgrade Shard at run start",
        "field": "shard_level",
        "max_level": 4,
        "base_cost": 55,
        "cost_step": 35,
    },
    "flasks": {
        "label": "Reserve Flask",
        "description": "+1 Healing Flask at run start (cap 3)",
        "field": "flask_level",
        "max_level": 1,
        "base_cost": 80,
        "cost_step": 0,
    },
    "armory": {
        "label": "Armory Expansion",
        "description": "+1 starting weapon slot",
        "field": "armory_level",
        "max_level": 2,
        "base_cost": 120,
        "cost_step": 90,
    },
    "ward": {
        "label": "Shrine Wards",
        "description": "+8 shrine core HP in defense mode",
        "field": "ward_level",
        "max_level": 5,
        "base_cost": 45,
        "cost_step": 30,
    },
    "idle": {
        "label": "Idle Imps",
        "description": "+6 gold/hour and more automated shrine crews",
        "field": "idle_level",
        "max_level": 5,
        "base_cost": 70,
        "cost_step": 45,
    },
}


def load_meta_progression(path: Path = META_PATH) -> MetaProgression:
    if not path.exists():
        return MetaProgression()
    try:
        payload = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return MetaProgression()
    if not isinstance(payload, dict):
        return MetaProgression()
    return MetaProgression(
        banked_gold=max(0, int(payload.get("banked_gold", 0))),
        patience_level=max(0, int(payload.get("patience_level", 0))),
        shard_level=max(0, int(payload.get("shard_level", 0))),
        flask_level=max(0, int(payload.get("flask_level", 0))),
        armory_level=max(0, int(payload.get("armory_level", 0))),
        ward_level=max(0, int(payload.get("ward_level", 0))),
        idle_level=max(0, int(payload.get("idle_level", 0))),
        last_idle_claim_ts=max(0, int(payload.get("last_idle_claim_ts", 0))),
    )


def save_meta_progression(meta: MetaProgression, path: Path = META_PATH) -> Path:
    path.write_text(json.dumps(meta.to_dict(), indent=2) + "\n")
    return path


def upgrade_cost(meta: MetaProgression, key: str) -> int | None:
    spec = META_UPGRADES.get(key)
    if not spec:
        return None
    level = getattr(meta, spec["field"])
    if level >= spec["max_level"]:
        return None
    return spec["base_cost"] + (level * spec["cost_step"])


def purchase_upgrade(meta: MetaProgression, key: str) -> tuple[bool, str]:
    spec = META_UPGRADES.get(key)
    if not spec:
        return False, "Unknown upgrade"
    cost = upgrade_cost(meta, key)
    if cost is None:
        return False, "Already maxed"
    if meta.banked_gold < cost:
        return False, f"Need {cost}g"

    meta.banked_gold -= cost
    current_level = getattr(meta, spec["field"])
    setattr(meta, spec["field"], current_level + 1)
    return True, f"{spec['label']} upgraded"


def deposit_run_gold(meta: MetaProgression, amount: int) -> int:
    deposited = max(0, amount)
    meta.banked_gold += deposited
    return deposited


def claim_idle_gold(
    meta: MetaProgression,
    *,
    now_ts: int | None = None,
    cap_seconds: int = 8 * 60 * 60,
) -> tuple[int, int]:
    """Deposit offline idle gold and return (gold_claimed, seconds_counted)."""
    now = int(now_ts if now_ts is not None else time.time())
    if meta.last_idle_claim_ts <= 0:
        meta.last_idle_claim_ts = now
        return 0, 0

    elapsed = max(0, min(cap_seconds, now - meta.last_idle_claim_ts))
    rate = meta.idle_gold_per_hour()
    if rate <= 0 or elapsed <= 0:
        meta.last_idle_claim_ts = now
        return 0, elapsed

    claimed = (elapsed * rate) // 3600
    if claimed > 0:
        meta.banked_gold += claimed
    meta.last_idle_claim_ts = now
    return claimed, elapsed
