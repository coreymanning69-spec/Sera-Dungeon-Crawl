# Project Vision

The near-term objective is a strong **autobattle-first dungeon loop** with transparent math.

## Priorities

- One shared combat legality engine for manual and auto actions.
- Fast replayability via deterministic seeded simulations.
- Clear player-facing logs explaining why outcomes happened.
- Endless mode progression tuned around patience pressure, not HP attrition.
- Shrine Defense as a base-defense loop with visible ASCII troops, turrets, idle crews, and endless horde pressure.
- Training Grounds as the primary combat-sim surface: configurable drills, seeded batches, build checks, and reward-bearing practice.
- Exportable combat/defense summaries that a future Phaser client can replay visually without owning simulation rules.

## Scope guardrails

- Keep the game pure Python with no external dependencies.
- Prefer small, testable systems over large framework rewrites.
- Delay story layer expansion until autobattle quality and balance are stable.
- Keep defense/idle systems small, deterministic, and tied to existing enemies, gold, and meta upgrades.
- Keep Python as the authoritative simulation engine until the browser client has a stable replay/spec contract.

See `docs/AUTOBATTLE_ROADMAP.md` for implementation sequencing.
