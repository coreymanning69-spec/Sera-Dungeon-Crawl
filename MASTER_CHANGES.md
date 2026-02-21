# Master Change Log

## Scope

This update adds a reproducible twenty-run analytics workflow to stress-test full game runs and capture where runs fail.

## What was added

1. **`scripts/run_twenty_games.py`**
   - Runs 20 new game sessions end-to-end with deterministic seeds.
   - Captures per-run and per-floor metrics:
     - floors cleared, turns taken, kills, ending patience
     - immunity events, misses, dodges, total damage dealt
     - materials found/used, upgrade shard spending, upgrades applied
   - Writes machine-readable and human-readable reports.

2. **`reports/twenty_game_analytics.json`**
   - Full structured dataset for all 20 runs.
   - Includes aggregate summary and complete per-run records.

3. **`reports/twenty_game_analytics.md`**
   - Compact master analytics report with aggregate KPIs, break analysis, per-run table, and balancing recommendations.

## Breakpoint findings from 20 completed games

- All 20 runs reached completion states (game over or victory).
- Current balance produced **0/20 victories** under automated progression.
- Dominant break behavior:
  - **Patience drain attrition** in long fights and high annoyance phases.
  - **Immunity lockout** when tag-gated enemies appear before the weapon has matching tags.
- Immediate balancing opportunities are documented in the report recommendations.

## Reproduction

```bash
python3 scripts/run_twenty_games.py
```

This regenerates both report files under `reports/`.
