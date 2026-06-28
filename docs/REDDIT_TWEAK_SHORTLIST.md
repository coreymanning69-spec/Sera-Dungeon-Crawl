# Reddit-Inspired Customization/Tweak Shortlist (Planning Draft)

I attempted to pull live Reddit threads from this environment, but outbound web access returned HTTP 403 on Reddit and general web endpoints. This list is a planning draft based on recurring customization/QoL themes that frequently surface in roguelike/ARPG Reddit communities.

## 10 tweaks players usually love

1. **Loadout presets (1-click swap)**
   - Save and load named weapon + gear + consumable setups.
   - Why players like it: experimentation without menu friction.
   - Potential integration: `play.py` menu flow + persistence in `sera/save.py`.

2. **Affix lock + reroll crafting**
   - Let players lock one affix while rerolling the other.
   - Why players like it: keeps “almost-good” drops relevant.
   - Potential integration: `sera/crafting.py`, `data/affixes.json` costs.

3. **Targeted loot focus (choose category bias)**
   - Before a floor, choose a loot bias (e.g., Divine tags, Bleed tools, Crit tools).
   - Why players like it: less junk RNG, more agency.
   - Potential integration: `sera/encounters.py` + loot generation weighting.

4. **Run mutators (opt-in challenge modifiers)**
   - Toggle mutators like "Enemies start casting" or "Patience decay +15%, loot rarity +1".
   - Why players like it: replayability and self-directed challenge.
   - Potential integration: `play.py` run setup + `sera/combat.py` turn hooks.

5. **Enemy intel panel / codex progress**
   - Show known vulnerabilities, seen abilities, and kill history.
   - Why players like it: long-term goals and strategic prep.
   - Potential integration: `sera/game_stats.py`, `sera/ui.py`, save-backed unlocks.

6. **Combat log filtering and pinning**
   - Filters: damage math, status changes, enemy intents, loot lines.
   - Why players like it: clarity during dense turns.
   - Potential integration: `sera/ui.py` render options + structured log categories.

7. **Auto-salvage rules**
   - Example: auto-salvage common weapons below base damage threshold.
   - Why players like it: less inventory cleanup.
   - Potential integration: `sera/loot_framework.py` and between-floor inventory actions.

8. **Skill tree style micro-perks (small permanent choices per floor)**
   - Pick one of three minor run perks each floor (e.g., +1 patience on kill chain).
   - Why players like it: steady customization arc even with bad drops.
   - Potential integration: new run-state perks in `play.py` and applied in combat/interest systems.

9. **Adaptive difficulty knobs**
   - Separate settings for enemy HP scaling, patience penalties, and reward multipliers.
   - Why players like it: tuning for fun, not one-size challenge.
   - Potential integration: `sera/damage_scale.py` and scenario setup surfaces.

10. **Transmog / flavor override for favorite weapon names**
    - Keep mechanics, change displayed name/flavor shell.
    - Why players like it: identity and attachment to builds.
    - Potential integration: presentation-only fields in `sera/weapon.py` + `sera/ui.py`.

## Suggested first 3 to prototype

1. **Loadout presets** (high QoL, low systems risk)
2. **Targeted loot focus** (high agency, moderate implementation)
3. **Run mutators** (high replayability, testable in scenarios)

## Validation plan if we implement any

- Keep logic deterministic in scripted scenarios where possible.
- Re-run all baseline scenarios from `main.py`.
- Add focused tests for save/load integrity and any new weighted RNG controls.
