"""Run analytics capture, persistence, and interactive review helpers."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ANALYTICS_DIR = Path("analytics")
ANALYTICS_INDEX_PATH = ANALYTICS_DIR / "analytics_index.json"


@dataclass
class TurnSnapshot:
    mode: str
    floor_or_wave: int
    turn: int
    patience: int
    total_kills: int
    total_damage: int
    source: str
    immune_streak: int = 0


@dataclass
class CombatEvent:
    kind: str
    floor_or_wave: int
    turn: int
    enemy_name: str
    weapon_name: str
    attempted_damage: int
    actual_damage: int
    outcome: str
    required_tag: str = ""


@dataclass
class MathIssue:
    kind: str
    detail: str
    floor_or_wave: int
    turn: int


@dataclass
class AnalyticsTracker:
    turn_snapshots: list[TurnSnapshot] = field(default_factory=list)
    combat_events: list[CombatEvent] = field(default_factory=list)
    issues: list[MathIssue] = field(default_factory=list)

    def capture_turn(
        self,
        *,
        mode: str,
        floor_or_wave: int,
        turn: int,
        patience: int,
        total_kills: int,
        total_damage: int,
        source: str,
        immune_streak: int = 0,
    ) -> None:
        self.turn_snapshots.append(
            TurnSnapshot(
                mode=mode,
                floor_or_wave=floor_or_wave,
                turn=turn,
                patience=patience,
                total_kills=total_kills,
                total_damage=total_damage,
                source=source,
                immune_streak=immune_streak,
            )
        )

    def record_combat_event(
        self,
        *,
        kind: str,
        floor_or_wave: int,
        turn: int,
        enemy_name: str,
        weapon_name: str,
        attempted_damage: int,
        actual_damage: int,
        outcome: str,
        required_tag: str = "",
    ) -> None:
        self.combat_events.append(
            CombatEvent(
                kind=kind,
                floor_or_wave=floor_or_wave,
                turn=turn,
                enemy_name=enemy_name,
                weapon_name=weapon_name,
                attempted_damage=attempted_damage,
                actual_damage=actual_damage,
                outcome=outcome,
                required_tag=required_tag,
            )
        )

    def record_issue(self, *, kind: str, detail: str, floor_or_wave: int, turn: int) -> None:
        self.issues.append(
            MathIssue(kind=kind, detail=detail, floor_or_wave=floor_or_wave, turn=turn)
        )

    def to_dict(self) -> dict:
        return {
            "turn_snapshots": [snapshot.__dict__ for snapshot in self.turn_snapshots],
            "combat_events": [event.__dict__ for event in self.combat_events],
            "issues": [issue.__dict__ for issue in self.issues],
        }


def _append_analytics_index(stamp: str, json_path: Path, csv_path: Path, tracker: AnalyticsTracker, index_path: Path) -> Path:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"exports": []}
    if index_path.exists():
        try:
            loaded = json.loads(index_path.read_text())
            if isinstance(loaded, dict) and isinstance(loaded.get("exports"), list):
                payload = loaded
        except json.JSONDecodeError:
            payload = {"exports": []}

    payload["exports"].append(
        {
            "timestamp_utc": stamp,
            "json_path": str(json_path),
            "csv_path": str(csv_path),
            "turn_count": len(tracker.turn_snapshots),
            "combat_event_count": len(tracker.combat_events),
            "issue_count": len(tracker.issues),
        }
    )
    payload["exports"] = payload["exports"][-25:]
    index_path.write_text(json.dumps(payload, indent=2) + "\n")
    return index_path


def export_analytics(tracker: AnalyticsTracker, *, output_dir: Path | str = ANALYTICS_DIR) -> tuple[Path, Path]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = target_dir / f"analytics_{stamp}.json"
    csv_path = target_dir / f"analytics_{stamp}.csv"

    json_path.write_text(json.dumps(tracker.to_dict(), indent=2) + "\n")

    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "mode",
                "floor_or_wave",
                "turn",
                "patience",
                "total_kills",
                "total_damage",
                "source",
                "immune_streak",
            ],
        )
        writer.writeheader()
        for snapshot in tracker.turn_snapshots:
            writer.writerow(snapshot.__dict__)

    _append_analytics_index(stamp, json_path, csv_path, tracker, target_dir / "analytics_index.json")
    return json_path, csv_path


def load_analytics_index(path: Path | str = ANALYTICS_INDEX_PATH) -> list[dict]:
    target = Path(path)
    if not target.exists():
        return []
    try:
        payload = json.loads(target.read_text())
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    exports = payload.get("exports", [])
    if not isinstance(exports, list):
        return []
    return [row for row in exports if isinstance(row, dict)]


def load_analytics_report(path: Path | str) -> dict:
    target = Path(path)
    if not target.exists():
        return {}
    try:
        payload = json.loads(target.read_text())
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def summarize_analytics_report(payload: dict, max_events: int = 8) -> list[str]:
    turn_snapshots = payload.get("turn_snapshots", []) if isinstance(payload, dict) else []
    combat_events = payload.get("combat_events", []) if isinstance(payload, dict) else []
    issues = payload.get("issues", []) if isinstance(payload, dict) else []

    lines = [
        f"Turns captured: {len(turn_snapshots)}",
        f"Combat events: {len(combat_events)}",
        f"Math issues: {len(issues)}",
    ]

    immune_events = [
        event for event in combat_events
        if isinstance(event, dict) and event.get("outcome") == "immune"
    ]
    if immune_events:
        lines.append(f"Immune hits: {len(immune_events)}")

    for event in combat_events[-max_events:]:
        if not isinstance(event, dict):
            continue
        tag_note = f" needs [{event.get('required_tag')}]" if event.get("required_tag") else ""
        lines.append(
            f"T{event.get('turn', '?')} {event.get('enemy_name', '?')}: "
            f"{event.get('outcome', '?')} {event.get('actual_damage', 0)}/{event.get('attempted_damage', 0)}{tag_note}"
        )

    return lines
