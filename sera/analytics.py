"""Run analytics capture and export helpers."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class TurnSnapshot:
    mode: str
    floor_or_wave: int
    turn: int
    patience: int
    total_kills: int
    total_damage: int
    source: str


@dataclass
class MathIssue:
    kind: str
    detail: str
    floor_or_wave: int
    turn: int


@dataclass
class AnalyticsTracker:
    turn_snapshots: list[TurnSnapshot] = field(default_factory=list)
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
            )
        )

    def record_issue(self, *, kind: str, detail: str, floor_or_wave: int, turn: int) -> None:
        self.issues.append(
            MathIssue(kind=kind, detail=detail, floor_or_wave=floor_or_wave, turn=turn)
        )

    def to_dict(self) -> dict:
        return {
            "turn_snapshots": [snapshot.__dict__ for snapshot in self.turn_snapshots],
            "issues": [issue.__dict__ for issue in self.issues],
        }


def export_analytics(tracker: AnalyticsTracker, *, output_dir: Path | str = "analytics") -> tuple[Path, Path]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = target_dir / f"analytics_{stamp}.json"
    csv_path = target_dir / f"analytics_{stamp}.csv"

    json_path.write_text(json.dumps(tracker.to_dict(), indent=2) + "\n")

    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["mode", "floor_or_wave", "turn", "patience", "total_kills", "total_damage", "source"],
        )
        writer.writeheader()
        for snapshot in tracker.turn_snapshots:
            writer.writerow(snapshot.__dict__)

    return json_path, csv_path
