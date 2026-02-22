# Master Verification Prompt (SERA Dungeon Crawl)

Use this prompt when you want a full coherence and survivability audit of the project.

---

You are auditing **SERA: ENDLESS ENGAGEMENT** for coherence, stability, and loop safety.

## Goals
1. Verify core game logic remains coherent across loading, combat, loot, floors, and mode transitions.
2. Execute scenario and interactive-path checks to find crash, dead-end, or quit-to-desktop paths.
3. Ensure every user-facing flow loops safely back to the title menu, even after errors or interrupts.
4. Confirm analytics persist before any shutdown-like event.
5. Validate each screen refreshes cleanly so the terminal behaves like a flashing screen, not a scrolling log.

## Constraints
- Python stdlib only.
- Respect architecture in `AGENTS.md` (data flow, deep copy convention, status/affix systems).
- Keep Sera voice rules intact.

## Required Verification Sequence
1. **Static pass**
   - Inspect `play.py`, `sera/ui.py`, `sera/game_stats.py`, `sera/save.py`, `main.py`.
   - Enumerate all early returns/exits and classify whether they route to menu, crash, or terminate process.
2. **Scenario logic checks**
   - Run:
     - `python3 main.py`
     - `python3 -c "from main import run_scenario_1, run_scenario_2, run_scenario_3; run_scenario_1(verbose=False); run_scenario_2(verbose=False); run_scenario_3(verbose=False); print('OK')"`
3. **Content loading sanity**
   - Run:
     - `python3 -c "from sera.loader import load_weapons, load_enemies, load_affixes; print(len(load_weapons()), 'weapons', len(load_enemies()), 'enemies', len(load_affixes()), 'affixes')"`
4. **UI rendering sanity**
   - Run:
     - `python3 -c "from sera import ui; print(ui.render_title_screen())"`
5. **Loop resilience checks**
   - Simulate quit tokens, menu backs, and interrupts.
   - Confirm each path recovers to title menu and does not terminate the process.
6. **Persistence checks**
   - Verify `game_stats.json` is updated when a run completes and when recovery events occur.

## Deliverables
- Summary of all risky control-flow paths found and outcome after fixes.
- List of tests run with pass/fail.
- Precise file/line citations for changes.
- Any remaining caveats (e.g., forced OS kill cannot be intercepted).
