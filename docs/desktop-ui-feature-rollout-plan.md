# Desktop UI + Systems Rollout Plan (10 Parts)

This plan is ordered so we can ship safely while preserving current combat behavior.

## 1) Stabilize baseline and add a reproducible test checklist

**Goal:** Lock current behavior before major UI/system work.

- Confirm all baseline scenarios pass.
- Add a reusable command checklist for regression runs.
- Record expected outputs for scenario summary metrics (`kills`, `patience`, `turns`, `game_over`).

**Deliverables:**
- `docs/` checklist for smoke + regression commands.
- Baseline scenario summaries committed for comparison.

**Done when:**
- `python3 main.py` runs cleanly.
- Silent scenario runs produce expected summary structure.

---

## 2) Add window-scaled UI layout primitives

**Goal:** Scale UI to terminal window size while preserving readability.

- Introduce a layout calculator that adapts panel widths/heights from detected viewport size.
- Keep minimum constraints so narrow windows still render valid fallback layout.
- Update main renderers to consume computed layout instead of fixed assumptions.

**Deliverables:**
- Layout helper(s) in `sera/ui.py`.
- Tests for small/medium/large viewport layout calculations.

**Done when:**
- Title, combat, and between-floors screens render at multiple dimensions without clipping errors.

---

## 3) Expand battle menu and add in-combat weapon switching

**Goal:** Improve player control options during battle.

- Add a new combat menu action: `Change Weapon`.
- Render weapon list with current/alternate options and return to combat loop correctly.
- Enforce valid selection and preserve turn/economy rules (no unintended free actions unless explicitly designed).

**Deliverables:**
- New battle menu option and handler in combat flow.
- UI renderer updates for weapon-switch prompt.
- Regression tests for weapon switching path.

**Done when:**
- User can switch to any owned weapon from battle menu and continue combat without state corruption.

---

## 4) Rename `Use healing potion` to `Access Potions` and add potion framework

**Goal:** Replace single-purpose heal action with extensible potion system.

- Update menu text and command routing to `Access Potions`.
- Create potion model (`name`, `description`, `charges`, `effect_type`, `effect_value`, `targeting_rules`).
- Add potion inventory in `GameState` and rendering list in battle UI.

**Deliverables:**
- New potion data model/module.
- Updated combat option labels and menu logic.
- Migration path from existing healing flasks to potion entries.

**Done when:**
- Old healing action is removed and replaced by potion submenu.

---

## 5) Implement core potion effects and usage rules

**Goal:** Make potion framework functional with multiple effect types.

- Implement at least:
  - `restore_patience` (healing)
  - `cleanse_debuff` (remove status)
  - `damage_boost_next_hit` (temporary buff)
- Validate eligibility (in combat only, available charges, legal target).
- Log effect outcomes to combat log in existing style.

**Deliverables:**
- Potion effect resolver.
- Integration with combat turn/state pipeline.
- Unit tests per effect and failure case.

**Done when:**
- All potion types apply predictable effects and decrement charges correctly.

---

## 6) Harden save menu flow: Save, Continue, Load are all operational

**Goal:** Make save/load UX explicit and reliable.

- Ensure title/menu and system menu both expose clear Save/Continue/Load actions where relevant.
- Validate that current run state (weapons, potion inventory, floor, patience, analytics snapshot) serializes/deserializes fully.
- Add graceful handling for missing/corrupt save file.

**Deliverables:**
- Unified save/load menu paths.
- Save schema updates for new potion framework and analytics fields.
- Tests for save-create, save-overwrite, load, missing-save recovery.

**Done when:**
- User can start, save, quit, continue/load, and resume same state deterministically.

---

## 7) Bake in analytics with explicit tracker assignments

**Goal:** Capture gameplay telemetry for balancing and UX improvements.

Trackers to add:
- **Run tracker:** run id, seed, start/end timestamps, mode.
- **Combat tracker:** turns, damage dealt/taken, interruptions, status applications.
- **Decision tracker:** menu selections, weapon swaps, potion uses, cancel/back frequency.
- **Economy tracker:** loot generated, items picked/skipped, crafting/material usage.
- **Survival tracker:** patience timeline, floor reached, game-over cause.

Implementation notes:
- Standard-library only JSON lines or batched JSON output.
- Optional local file sink with session rotation.
- Keep analytics writes non-blocking from UX perspective.

**Deliverables:**
- `sera/analytics.py` module (or equivalent) with tracker interfaces.
- Event emission points wired into gameplay flow.
- Schema documentation in `docs/`.

**Done when:**
- Full run produces analytics artifact with all required event categories.

---

## 8) Add comprehensive option-level tests for all new menu paths

**Goal:** Verify each user option works end-to-end.

Must-test options:
- Battle: attack, change weapon, access potions, any existing defend/utility actions.
- Menus: save, continue, load, quit/cancel/back transitions.
- Error handling: invalid input, empty potion inventory, invalid weapon index.

**Deliverables:**
- Automated tests covering each option route.
- Command-level smoke checks in docs for local validation.

**Done when:**
- Option-level tests pass and no menu path dead-ends the game loop.

---

## 9) UX polish and consistency pass

**Goal:** Make interface clean, consistent, and readable after feature additions.

- Standardize labels and ordering across battle/system menus.
- Keep Sera-voice flavor lines consistent with existing rules.
- Improve spacing/dividers for scaled layouts and longer menu lists.
- Verify overlay behavior for blocking vs non-blocking menus remains coherent.

**Deliverables:**
- Updated UI text and render formatting.
- Final pass on help prompts and key hints.

**Done when:**
- UI feels coherent and all menu labels/flows are self-explanatory.

---

## 10) Release gate: regression, analytics validation, and rollout checklist

**Goal:** Ship safely with confidence.

- Run full regression suite + scenario scripts.
- Validate save/load persistence across multiple sessions.
- Validate analytics data quality (no missing required fields, stable schema).
- Produce rollout checklist with known risks and fallback plan.

**Deliverables:**
- Final verification report in `docs/`.
- Tagged release candidate commit.

**Done when:**
- All gates pass and there is a documented rollback path.

---

## Suggested execution rhythm

- **Sprint 1:** Parts 1-3 (foundation + UI scaling + weapon switch)
- **Sprint 2:** Parts 4-6 (potions + save/load hardening)
- **Sprint 3:** Parts 7-10 (analytics + tests + polish + release)
