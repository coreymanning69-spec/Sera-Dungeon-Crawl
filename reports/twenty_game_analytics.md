# Twenty-Game Analytics Report

- Runs: **20**
- Victories: **0**
- Losses: **20**
- Avg floors cleared: **1.75**
- Avg turns (cumulative run count): **44.8**
- Avg damage dealt: **64.5**
- Total immunity events: **27**
- Total misses: **50**
- Total dodges: **129**

## Break Analysis

- Losses caused by immunity lockout: **6**
- Losses caused by patience drain (non-immunity): **14**
- Dominant failure mode: progression can stall when a run reaches tag-gated enemies without matching weapon tags.

## Per-Run Summary

| Game | Seed | Start Weapon | Final Weapon | Floors | Victory | Patience | Immune | Miss | Dodge | Damage | Break Reason |
|---:|---:|---|---|---:|:---:|---:|---:|---:|---:|---:|---|
| 1 | 90211 | Blessed Mace +1 | Blessed Mace +1 | 2 | N | 0 | 0 | 4 | 10 | 53 | Game over from patience drain |
| 2 | 90212 | Sonic Bell | Moonlit Spectral Scythe | 1 | N | 7 | 0 | 1 | 7 | 69 | Game over from patience drain |
| 3 | 90213 | Molten Flail +1 | Molten Flail +1 | 2 | N | 0 | 0 | 1 | 2 | 94 | Game over from patience drain |
| 4 | 90214 | Thunderclap Gauntlet | Petty Blessed Mace +1 | 2 | N | 0 | 7 | 1 | 10 | 33 | Game over after repeated immunity lockout |
| 5 | 90215 | Bone Whip | Spectral Scythe of Hemorrhage +1 | 1 | N | 0 | 0 | 5 | 10 | 36 | Game over from patience drain |
| 6 | 90216 | Iron Claymore +1 | Iron Claymore +1 | 2 | N | 0 | 0 | 1 | 12 | 83 | Game over from patience drain |
| 7 | 90217 | Molten Flail | Cruel Runic Greataxe +1 | 2 | N | 0 | 4 | 0 | 4 | 69 | Game over after repeated immunity lockout |
| 8 | 90218 | Shadow Needle | Stormglass Wand | 1 | N | 0 | 0 | 2 | 5 | 43 | Game over from patience drain |
| 9 | 90219 | Frozen Scepter | Moonlit War Maul of Execution | 2 | N | 0 | 0 | 3 | 6 | 56 | Game over from patience drain |
| 10 | 90220 | Forbidden Tome | Venomous Iron Claymore +1 | 2 | N | 0 | 4 | 1 | 4 | 64 | Game over after repeated immunity lockout |
| 11 | 90221 | Frozen Scepter | Chain Hook of the First Strike +1 | 2 | N | 0 | 6 | 1 | 2 | 61 | Game over after repeated immunity lockout |
| 12 | 90222 | Molten Flail +1 | Molten Flail +1 | 1 | N | 0 | 0 | 2 | 3 | 68 | Game over from patience drain |
| 13 | 90223 | Blessed Mace +1 | Blessed Mace +1 | 2 | N | 0 | 0 | 3 | 6 | 74 | Game over from patience drain |
| 14 | 90224 | War Maul +1 | War Maul +1 | 2 | N | 0 | 0 | 4 | 8 | 77 | Game over from patience drain |
| 15 | 90225 | Acid Vial | Spirit Lantern +1 | 2 | N | 0 | 1 | 2 | 13 | 49 | Game over after repeated immunity lockout |
| 16 | 90226 | Blessed Mace | Blessed Mace of Frost +1 | 2 | N | 0 | 0 | 7 | 5 | 87 | Game over from patience drain |
| 17 | 90227 | War Maul +1 | War Maul +1 | 2 | N | 0 | 0 | 6 | 3 | 84 | Game over from patience drain |
| 18 | 90228 | Blessed Mace +2 | Blessed Mace +2 | 3 | N | 0 | 0 | 2 | 11 | 94 | Game over from patience drain |
| 19 | 90229 | Venom Fang Dagger | Venom Fang Dagger | 0 | N | 0 | 0 | 3 | 5 | 36 | Game over from patience drain |
| 20 | 90230 | Runic Greataxe | Iron Claymore of Doom | 2 | N | 0 | 5 | 1 | 3 | 60 | Game over after repeated immunity lockout |

## Recommendations

1. Add a guaranteed tag-repair action before floor 4+ (crafting fallback or mercy tag infusion).
2. Weight loot generation toward missing vulnerability tags when immunity events are detected in-combat.
3. Consider a soft-fail rule: first immune hit in an encounter grants a one-time material drop for counterplay.
