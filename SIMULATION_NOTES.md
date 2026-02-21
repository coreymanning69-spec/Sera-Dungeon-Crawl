# Simulation Review (5 Runs)

I ran `python3 main.py` five times and compared the scenario summaries.

## Observations

1. **All five runs produced the same high-level outcomes** in every scenario summary line.
2. **Scenario 1 consistently ends with one kill after 3 turns** (`Result: 1 kills, 86 Patience remaining`).
3. **Scenario 3 summary reports boss HP as `50/50` after combat every time**, even though combat log lines show the boss taking damage.
4. **Scenario 4 summary reports golem HP as `34/34` after combat every time**, even though combat log lines show repeated hits for damage.
5. No crashes occurred during any run.

## Areas for improvement / clarification

- **Clarify scenario API in docs:** `AGENTS.md` says scenarios support `verbose=False`, but current `run_scenario_1..4()` signatures do not accept a `verbose` argument. Add the parameter or update docs to avoid confusion.
- **Fix post-combat HP reporting in Scenario 3 and 4:** the printed `boss.current_hp` / `golem.current_hp` values appear to come from template objects, not the combat-mutated copies. Print HP from combat results (or returned enemy state) instead.
- **Clarify deterministic vs random intent:** five repeated runs gave identical summaries. If this is intentional (scripted demo), say so in `main.py` header/help text. If not intentional, seed/choice points may need review.
- **Scenario 1 expectation text could be clarified:** intro mentions “multi-kill overkill” but summary result is one kill in three turns. Either extend turn limit or adjust wording.
- **Add machine-readable scenario returns:** returning structured dicts from `run_scenario_1..4()` (as AGENTS docs suggest) would make repeated validation and regression checks easier.
