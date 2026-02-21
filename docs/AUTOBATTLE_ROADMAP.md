# Autobattle Roadmap

This roadmap replaces older one-off planning notes and focuses only on work that is still open.

## Current baseline

- Auto-battle exists in the playable loop (`play.py`) and can clear encounters.
- Core combat legality already lives in shared engine modules (`sera/combat.py`, `sera/enemy.py`, `sera/weapon.py`).
- Existing scenario demos in `main.py` cover deterministic combat checks.

## Next milestones

### 1) Rule parity pass (manual vs auto)

**Goal:** Ensure auto-battle and manual battle obey the same damage, permission, and status rules.

- Compare manual and auto resolution paths for:
  - permission failures,
  - status application timing,
  - patience gain/loss side effects,
  - kill/overkill accounting.
- Add targeted tests for parity edge cases.

**Exit criteria:** No known legality differences remain except intentionally documented AI decision behavior.

### 2) Decision quality v1

**Goal:** Make auto-battle stop making obviously bad tactical choices.

- Prioritize targets by kill potential and threat.
- Prefer weapons that satisfy current enemy vulnerability constraints.
- Add conservative consumable usage thresholds.

**Exit criteria:** In repeated seeded runs, auto-battle survives deeper on average than current baseline.

### 3) Telemetry and explainability

**Goal:** Make auto-battle outcomes debuggable.

- Add structured reason codes for AI choices (target selected, weapon selected, consumable used).
- Surface short explanation lines in combat log output.
- Record summary metrics per run (turns, kills, damage, patience swings).

**Exit criteria:** A failed run can be reviewed without reproducing interactively.

### 4) Balance feedback loop

**Goal:** Tune numbers with measurable signals.

- Add a reproducible simulation command for seeded batches.
- Capture floor-by-floor survival and time-to-kill metrics.
- Feed findings back into encounter pacing and loot/crafting pacing.

**Exit criteria:** Autobattle has stable progression through early floors and reaches intended failure/success bands.

## Definition of done for autobattle phase

- Rule parity validated by tests.
- Decision behavior is deterministic under fixed seeds.
- Metrics pipeline exists for fast balancing iterations.
- User-facing copy clearly states autobattle is convenience-first, not perfect play.
