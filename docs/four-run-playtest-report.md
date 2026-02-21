# Four-Run Gameplay Playtest Report

## Purpose

Run four fresh game sessions from `play.py` to completion (victory or game over) or error state, then capture reliability notes and improvement opportunities for a later comprehensive documentation pass.

## Method

I used an automated input harness against `play.run_new_game_session()` with fixed seeds so each run was reproducible:

- Seeds: `200`, `201`, `202`, `203`
- Combat strategy: always select auto-battle (`a`) when available
- Choice strategy: pick `[1]` for numbered menus and `y` for loot prompts
- Session end handling: force return to title after each run so all four runs execute cleanly

This is intentionally a "baseline autopilot" pass focused on stability and rough flow, not optimal play.

## Results (4 runs)

| Run | Seed | End state | Floor reached | Kills | Turns survived | Patience at end | Errors |
|---|---:|---|---:|---:|---:|---|---|
| 1 | 200 | Game Over | 5 | 7 | 44 | 0/100 | None |
| 2 | 201 | Game Over | 4 | 5 | 26 | 0/100 | None |
| 3 | 202 | Game Over | 5 | 8 | 40 | 0/100 | None |
| 4 | 203 | Game Over | 4 | 4 | 24 | 0/100 | None |

### Stability summary

- **Hard crashes/exceptions:** none in all four runs
- **Soft failures:** none that blocked progression
- **Outcome trend:** all four runs ended via patience depletion (no victories)

## Findings and areas for improvement

### 1) Run statistics under-report damage during auto-battle

Observed in all four runs: `Run Statistics` showed `Total Damage Dealt: 0` despite non-zero kills.

Likely cause:
- Manual attacks record damage via `run_stats.record_damage(actual)` in `_resolve_attack()`.
- Auto-battle path `_run_auto_battle_burst()` tracks local `total_damage_dealt` for its own summary but does not write into `state.run_stats`.

Impact:
- End-of-run analytics are misleading for players who use auto-battle heavily.

Suggested fix:
- In `_run_auto_battle_burst()`, call `state.run_stats.record_damage(actual)` after each successful hit.

### 2) Auto-battle-first behavior tends to lose by floor 4–5

All four autopilot runs failed before victory.

Interpretation:
- This may be expected for a low-decision strategy, but it suggests auto-battle may not make tactical choices around:
  - target prioritization,
  - weapon/equipment swapping,
  - crafting/upgrade timing,
  - healing flask timing.

Suggested follow-up:
- Clarify in UI text that auto-battle is a convenience mode, not a smart tactical assistant.
- Optionally add a "safe auto" heuristic (focus low HP targets, use flask under threshold).

### 3) Good reliability baseline for continued balancing

Despite aggressive automation and many state transitions (combat, loot, between-floor menus, equipment generation), runs remained stable with no exceptions.

## Recommended next pass scope

For the comprehensive pass, pair this report with:

1. **A manual playtest pass** (4 runs with intentional build decisions)
2. **A metrics pass** comparing manual vs auto outcomes
3. **A stats integrity pass** ensuring all combat paths feed `RunStats` consistently
4. **A UX copy pass** clarifying what auto-battle does and does not optimize

## Reproduction commands

```bash
# Baseline simulation sanity check
python3 main.py

# Four-run automated playtest harness (used for this report)
python3 - <<'PY'
import random,re,io,contextlib
import play

def run_one(seed:int):
    random.seed(seed)
    def chooser(prompt, valid):
        if valid is None:
            return ''
        if 'a' in valid:
            return 'a'
        if set(valid)=={'y','n'}:
            return 'y'
        if '1' in valid:
            return '1'
        return valid[0]

    orig_get_choice=play.get_choice
    orig_pause=play.pause
    orig_clear=play.ui.clear
    orig_closing=play._show_closing_menu

    play.get_choice=lambda prompt='> ', valid=None: chooser(prompt,valid)
    play.pause=lambda msg='': None
    play.ui.clear=lambda: None
    play._show_closing_menu=lambda title, quote: 'title'

    buf=io.StringIO()
    err=None
    try:
        with contextlib.redirect_stdout(buf):
            play.run_new_game_session()
    except Exception as e:
        err=repr(e)
    finally:
        play.get_choice=orig_get_choice
        play.pause=orig_pause
        play.ui.clear=orig_clear
        play._show_closing_menu=orig_closing

    text=buf.getvalue()
    m_floor=re.search(r'Died on floor:\s*(\d+)',text)
    m_kills=re.search(r'Total kills:\s*(\d+)',text)
    m_turns=re.search(r'Turns survived:(\d+)',text)
    m_pat=re.search(r'Current Patience:\s*(\d+/\d+)',text)
    m_dmg=re.search(r'Total Damage Dealt:\s*(\d+)',text)
    return {
        'seed': seed,
        'error': err,
        'died_floor': int(m_floor.group(1)) if m_floor else None,
        'kills': int(m_kills.group(1)) if m_kills else None,
        'turns': int(m_turns.group(1)) if m_turns else None,
        'patience': m_pat.group(1) if m_pat else None,
        'total_damage': int(m_dmg.group(1)) if m_dmg else None,
    }

for seed in [200,201,202,203]:
    print(run_one(seed))
PY
```
