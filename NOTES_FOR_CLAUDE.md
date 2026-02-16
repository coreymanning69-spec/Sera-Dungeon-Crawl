# Notes for Claude — Optimization + Meta Commentary

This pass focused on **small, low-risk runtime cleanup** and documenting where future work is highest impact.

## What was optimized in this pass

1. **Defense calculations are now reusable per phase/turn** in `play.py`.
   - Added `_build_defense_profile(state, stats=None)` that computes:
     - flat annoyance reduction,
     - general resistance,
     - elemental resistance map.
   - This removes repeated recomputation of `total_resistances()` and related values in hot combat paths.

2. **Enemy phase in manual combat now reuses one defense profile**.
   - In `run_combat`, the profile is computed once before iterating enemy actions.
   - `_resolve_enemy_action(...)` accepts an optional precomputed defense profile.

3. **Auto-battle burst now reuses one defense profile per turn**.
   - The same defense map is reused for all enemy actions during that turn.

## Why this matters

- `EquipmentLoadout.total_resistances()` builds a dictionary each call. In combat loops, that can be called many times per turn.
- `GameState.final_stats` builds a derived stat object; avoiding repeated calls in inner loops reduces overhead and keeps behavior deterministic.
- This pass intentionally avoids balance changes and focuses only on reducing repeated calculations.

## Key architecture observations

1. **`play.py` is currently a god-file** (state management + combat orchestration + menus + I/O).
   - Refactor candidate: split into modules:
     - `game_state.py`
     - `combat_runtime.py`
     - `menus.py`
     - `save_system.py`

2. **State is mutable and shared in many paths**.
   - Great for rapid iteration, but harder to test and reason about.
   - Consider pure helper functions for battle resolution chunks to make regression tests easier.

3. **Manual and auto-combat logic are parallel but not unified**.
   - They already diverge in mechanics details.
   - Consider a shared lower-level resolver that both paths call, with optional verbosity/UI hooks.

## Suggested next optimization targets (safe)

1. Cache or memoize `state.final_stats` behind a dirty flag that invalidates only when equipment changes.
2. Centralize "annoyance mitigation" formula into one function to guarantee consistent math between manual and auto modes.
3. Reduce repeated list rebuilds (`[e for e in enemies if e.current_hp > 0]`) in loops by maintaining an alive index list when practical.

## Suggested gameplay/system targets (bigger scope)

1. Add save/load serializer for full `GameState`.
2. Consolidate overkill handling so splash/cleave and patience restoration come from one canonical function.
3. Add startup validation ensuring enemy vulnerabilities always map to obtainable tag sources (weapons/materials/affixes).

---

If you pick this up next, the least risky continuation is:
- add a `compute_annoyance_cost(...)` helper,
- then route both manual and auto paths through it,
- then add tests for mitigation edge cases.
