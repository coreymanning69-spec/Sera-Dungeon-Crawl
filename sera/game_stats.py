"""Persistent game statistics across runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_GAME_STATS_PATH = Path("game_stats.json")


# ─────────────────────────────────────────────────────────
# Schema helpers
# ─────────────────────────────────────────────────────────

def _default_overall() -> dict:
    return {
        "total_runs": 0,
        "wins": 0,
        "losses": 0,
        "total_kills": 0,
        "total_turns": 0,
        "total_damage": 0,
        "best_floor": 0,
        "best_wave": 0,
        "best_overkill": 0,
        "weapons_found": 0,
        "materials_used": 0,
    }


def default_stats_payload() -> dict:
    return {
        "last_run": None,
        "overall": _default_overall(),
    }


def load_game_stats(path: Path | str = DEFAULT_GAME_STATS_PATH) -> dict:
    target = Path(path)
    if not target.exists():
        return default_stats_payload()

    try:
        data = json.loads(target.read_text())
    except json.JSONDecodeError:
        return default_stats_payload()

    if not isinstance(data, dict):
        return default_stats_payload()

    payload = default_stats_payload()
    if isinstance(data.get("last_run"), dict):
        payload["last_run"] = data["last_run"]

    overall = data.get("overall", {})
    if isinstance(overall, dict):
        payload["overall"].update({k: overall.get(k, v) for k, v in payload["overall"].items()})

    return payload


def save_game_stats(data: dict, path: Path | str = DEFAULT_GAME_STATS_PATH) -> Path:
    target = Path(path)
    target.write_text(json.dumps(data, indent=2) + "\n")
    return target


# ─────────────────────────────────────────────────────────
# Aggregation
# ─────────────────────────────────────────────────────────

def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def merge_run_stats(
    payload: dict,
    run_summary: dict,
    *,
    path: Path | str = DEFAULT_GAME_STATS_PATH,
) -> dict:
    payload.setdefault("overall", _default_overall())
    payload["last_run"] = run_summary

    overall = payload["overall"]
    overall["total_runs"] = _to_int(overall.get("total_runs")) + 1

    won = bool(run_summary.get("won", False))
    if won:
        overall["wins"] = _to_int(overall.get("wins")) + 1
    else:
        overall["losses"] = _to_int(overall.get("losses")) + 1

    overall["total_kills"] = _to_int(overall.get("total_kills")) + _to_int(run_summary.get("total_kills"))
    overall["total_turns"] = _to_int(overall.get("total_turns")) + _to_int(run_summary.get("total_turns"))
    overall["total_damage"] = _to_int(overall.get("total_damage")) + _to_int(run_summary.get("total_damage"))
    overall["weapons_found"] = _to_int(overall.get("weapons_found")) + _to_int(run_summary.get("weapons_found"))
    overall["materials_used"] = _to_int(overall.get("materials_used")) + _to_int(run_summary.get("materials_used"))

    overall["best_floor"] = max(_to_int(overall.get("best_floor")), _to_int(run_summary.get("floors_cleared")))
    overall["best_wave"] = max(_to_int(overall.get("best_wave")), _to_int(run_summary.get("wave_reached")))
    overall["best_overkill"] = max(_to_int(overall.get("best_overkill")), _to_int(run_summary.get("best_overkill")))

    save_game_stats(payload, path)
    return payload


def stamp_run_summary(base_summary: dict, *, won: bool, mode: str, seed: int) -> dict:
    summary = dict(base_summary)
    summary["won"] = won
    summary["mode"] = mode
    summary["seed"] = seed
    summary["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    return summary
