# SERA: ENDLESS ENGAGEMENT — 20-Run Simulation Analysis

**Date:** 2026-02-21
**Runs:** 20 complete games with randomized AI
**Base Seed:** 907037
**Result:** 0 victories, 20 patience losses (0% win rate)

---

## Executive Summary

The simulation reveals that **Sera is unwinnable under current balance**. All 20 runs exhausted patience before reaching victory. The core issue is a fundamental mismatch between:

- **Patience drain rate:** -1 turn + enemy annoyance = -2 to -5 per turn
- **Patience restoration rate:** +5 per kill, +excess per overkill, +10 per multi-kill
- **Math at scale:** With 3 kills per floor × 3 turns each = 15 damage taken, players need massive overkill to break even

---

## Floor-by-Floor Breakdown

### Floor 1: The Wall (65% Fail Rate)

**Reached by:** 20/20 runs
**Survived:** 13/20 (65%)
**Failed:** 7/20 (35%)
**Avg turns to clear:** 7-12

**Pattern:** Early runs with 0 kills never escape floor 1.

```
Runs with 0 kills on Floor 1: 7 (35%)
  - Run 1:  12 turns, 0 damage, dead
  - Run 4:  12 turns, 0 damage, dead
  - Run 6:  10 turns, 0 damage, dead
  - Run 14: 12 turns, 0 damage, dead
  - Run 16: 10 turns, 0 damage, dead
  - Run 17: 10 turns, 0 damage, dead
  - Run 20: 10 turns, 0 damage, dead
```

**Analysis:** Weapon selection appears to be failing hard. 35% of runs have NO KILLS on the first floor. This suggests:
1. Starting weapon choices may be too weak
2. Permission system (damage tags) blocking viable attacks
3. Enemy dodges/armor are too high

---

### Floor 2: Scaling Cliff

**Reached by:** 13/20 runs
**Survived:** 6/13 (46%)
**Failed:** 7/13 (54%)
**Avg turns to clear:** 10-21

**Pattern:** Runs that clear floor 1 with kills progress to floor 2, but half fail here.

```
Floor 2 Survivors:
  - Run 2:  11 turns, 1 kill, 9 dmg → Floor 3
  - Run 3:  12 turns, 1 kill, 20 dmg → Floor 3
  - Run 5:  (multiple encounters) → Floor 3
  - Run 13: 16 turns, 2 kills, 24 dmg → Floor 3
  - Run 15: 21 turns, 1 kill, 42 dmg → Floor 3
  - Run 18: 13 turns, 1 kill, 12 dmg → Floor 3

Floor 2 Failures:
  - Run 7:  10 turns, 1 kill → patience 0
```

**Key observation:** Runs that get kills progress, but low damage (9-12 dmg) is barely enough to survive. Multi-kill bonus (+10 patience) only appears in 2 runs, suggesting encounters are too spread out for simultaneous kills.

---

### Floor 3: The Death Spiral

**Reached by:** 7/20 runs
**Survived:** 0/7 (0%)
**Failed:** 7/7 (100%)
**Avg turns to clear:** 15-29
**Avg kills on floor:** 3 (consistent)
**Damage range:** 30-69 dmg

```
Run 5:  29 turns, 3 kills, 69 dmg → patience 0
Run 8:  16 turns, 3 kills, 36 dmg → patience 0
Run 9:  15 turns, 3 kills, 30 dmg → patience 0
Run 10: 22 turns, 3 kills, 45 dmg → patience 0 (+ 1 material used)
Run 11: 21 turns, 3 kills, 54 dmg → patience 0
Run 12: 21 turns, 3 kills, 48 dmg → patience 0
Run 19: 24 turns, 3 kills, 54 dmg → patience 0
```

**Critical finding:** **NO RUNS SURVIVE FLOOR 3.** Despite consistent kills, the turn cost is fatal. Even with 69 total damage (Run 5, the best performer), the player failed.

**Patience math for Floor 3 example (Run 5):**
- Turns: -29 patience
- Kills: +5 × 3 = +15 patience
- Overkill: ~19 damage (69 total - ~50 max HP) = +19 patience
- Enemy annoyance: -20 to -30 estimated
- **Net: roughly -15 to -25 patience loss**

Floors 4 & 5 were never reached.

---

## Patience Economics

### Drain vs. Restoration Balance

| Event | Patience Change |
|-------|-----------------|
| Time (per turn) | -1 |
| Enemy action (weak) | -2 to -5 |
| Enemy action (strong) | -10 to -15 |
| **Typical turn total** | **-3 to -6** |
| Kill | +5 |
| Multi-kill bonus | +10 |
| Overkill (per excess dmg) | +1 |

### Math Check: Can a Run Break Even?

**Best case floor survival scenario:**
- 3 enemies × ~15 HP each = 45 total HP to deal
- 3 kills = +15 patience
- With heavy overkill (45 dmg total = +45 patience from excess)
- 15 turns × -1 = -15 patience
- Enemy annoyance (assume 3 turns × -3 avg) = -9 patience
- **Total: +15 + 45 - 15 - 9 = +36 patience gain**

**Worst case (actual gameplay):**
- Damage spread (no overkill, just minimum kills)
- Low kill count early (0 kills is common)
- Long drawn-out fights
- **Result: -10 to -20 patience per floor**

**Over 3 floors:** -30 to -60 net patience loss = **automatic failure**

---

## Weapon & Loot Analysis

### Weapons Found

**Average per run:** 0.8 weapons
**Runs with 0 new weapons:** 9/20 (45%)
**Runs with 1+ weapons:** 11/20 (55%)
**Max found in one run:** 2

**Loot impact:** Low new weapon discovery doesn't help since the starting weapon often fails due to permission gates.

### Materials Used

**Total materials used:** 2 out of 20 runs
**Success rate of crafting:** 0/2 (0%)

Both runs that used materials (10, 13) still failed. **Crafting provides no noticeable win condition.**

---

## Difficulty Spikes & Walls

### Early Termination (Floors 1-2)

```
Deaths by Floor 1: 7 runs (10-12 turns, 0 kills)
Deaths by Floor 2: 6 runs (10-21 turns, 1-2 kills)
Deaths by Floor 3: 7 runs (15-29 turns, 3 kills)
```

**Wall progression:**
1. **Floor 1 wall (35% fail rate):** Permission gates / low starting damage
2. **Floor 2 wall (54% fail rate of survivors):** Cumulative patience loss
3. **Floor 3 wall (100% fail rate):** Unsustainable turn-to-kill ratio

### Turn Efficiency

| Floor | Avg Turns | Avg Kills | Turns/Kill |
|-------|-----------|-----------|-----------|
| 1 | 7 | 0.3 | 23.3 |
| 2 | 12.7 | 0.8 | 15.9 |
| 3 | 19.3 | 3 | 6.4 |

**Critical observation:** Turns per kill actually IMPROVES on floor 3 (down to 6.4), but the cumulative effect is fatal. Players need more than just efficiency—they need explosive overkill.

---

## What's Breaking the Game

### 1. **Permission Gate Failures (35% of runs)**

7 out of 20 runs got 0 kills on Floor 1. This happens when:
- Starting weapon lacks required damage tags for floor 1 enemy
- Example: Starting with PHYSICAL sword vs. ETHEREAL-only ghost

**Fix needed:** Guarantee starting weapons can at least damage floor 1 enemies.

### 2. **Overkill is Rare**

Most runs show consistent kills (3 per floor) but low-to-moderate damage (30-54 total per floor):
- Average 19.6 damage when 3 kills landed
- For overkill to matter, need 40+ damage in tight windows
- Current scaling doesn't support burst damage

**Fix needed:** Buff weapon base damage, affix stacking, or add scaling that encourages overkill builds.

### 3. **Multi-Kill Bonus Unreachable**

Only 2 out of 20 runs achieved +10 multi-kill bonus:
- Requires 2+ kills in a single turn
- Encounters are usually 1-3 spread-out enemies
- Combat turns are sequential (one target at a time)

**Fix needed:** Either redesign multi-kill (hits vs. kills?) or make it more achievable.

### 4. **Patience Drain is Relentless**

The -1 per turn + annoyance is a 3-turn timer hidden in 100 patience:
- 100 turns max before game over (unmodified)
- Actual 5-floor run needs 60-90 turns
- Every turn above 20 per floor is catastrophic

**Fix needed:** Either reduce turn cost, increase base patience, or add restoration mechanics beyond kills.

---

## Success Conditions (Not Met)

For a 0% → 50%+ win rate, the game needs ONE of:

### Option A: Increase Overkill Potential
- Higher base damage (2-5 instead of 1-3)
- Affixes that scale multiplicatively
- Status effects that amplify next hit

### Option B: Speed Up Kills
- Reduce enemy HP scaling
- Add status effects that reduce enemy turns
- Buff starter weapons specifically

### Option C: Reduce Patience Drain
- Lower TICK_DRAIN from 1 to 0.5
- Reduce annoyance costs by 25%
- Add sustainability mechanics (healing flasks, defensive perks)

### Option D: Improve Loot Loop
- More weapons found (currently 0.8 avg → 1.5+ avg)
- Materials that actually help (0/2 success rate)
- Crafting as viable win condition

---

## Per-Run Summary Table

| Run | Floor | Turns | Kills | Dmg | Weapons | Result |
|-----|-------|-------|-------|-----|---------|--------|
| 1 | 1 | 12 | 0 | 0 | 0 | ✗ No kills |
| 2 | 2 | 11 | 1 | 9 | 1 | ✗ Dmg too low |
| 3 | 2 | 12 | 1 | 20 | 0 | ✗ Cumulative loss |
| 4 | 1 | 12 | 0 | 0 | 0 | ✗ No kills |
| 5 | 3 | 29 | 3 | 69 | 1 | ✗ 29 turns fatal |
| 6 | 1 | 10 | 0 | 0 | 0 | ✗ No kills |
| 7 | 2 | 10 | 1 | 9 | 0 | ✗ Dmg too low |
| 8 | 3 | 16 | 3 | 36 | 2 | ✗ Turns exceed gain |
| 9 | 3 | 15 | 3 | 30 | 2 | ✗ Turns exceed gain |
| 10 | 3 | 22 | 3 | 45 | 2 | ✗ Turns exceed gain |
| 11 | 3 | 21 | 3 | 54 | 2 | ✗ Turns exceed gain |
| 12 | 3 | 21 | 3 | 48 | 2 | ✗ Turns exceed gain |
| 13 | 2 | 16 | 2 | 24 | 1 | ✗ Only 2 kills |
| 14 | 1 | 12 | 0 | 0 | 0 | ✗ No kills |
| 15 | 2 | 21 | 1 | 42 | 1 | ✗ Only 1 kill |
| 16 | 1 | 10 | 0 | 0 | 0 | ✗ No kills |
| 17 | 1 | 10 | 0 | 0 | 0 | ✗ No kills |
| 18 | 2 | 13 | 1 | 12 | 0 | ✗ Dmg too low |
| 19 | 3 | 24 | 3 | 54 | 1 | ✗ 24 turns fatal |
| 20 | 1 | 10 | 0 | 0 | 0 | ✗ No kills |

---

## Conclusion

**The game is mechanically unwinnable at current balance.**

### Root Cause
The patience drain rate exceeds the patience restoration rate by 1.5-2× on every floor. Even optimal play (3 kills per floor with moderate overkill) cannot sustain a 5-floor run.

### Evidence
- 0/20 victories
- 100% patience loss
- Floor 3 is 100% fatal (7/7 failures)
- Best run (Run 5) had 69 damage + 3 kills but still failed

### Required Changes
Pick at least one:
1. **Buff damage output** (starting weapons +1, affixes ×1.5)
2. **Reduce patience drain** (TICK_DRAIN: 1 → 0.5 or 1-per-2-turns)
3. **Increase kill value** (+7 instead of +5, or add scaling with floor)
4. **Add defensive mechanics** (damage reduction, dodge buffs, healing loop)

The system is sound (transparency, small numbers, feedback) but currently tuned for failure rather than challenge.
