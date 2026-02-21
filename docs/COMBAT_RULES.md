# Combat Rules (Revision 1.10)

## Damage pipeline
1. Base damage
2. Scaling contribution
3. Upgrade contribution
4. Element interaction modifier
5. Resistance stack + multiplier + cap clamp
6. Final damage
7. Effects resolve independently (can apply even if damage is 0)

## Element rules
- Elements: Fire, Air, Water, Ice, Earth, Divine.
- Opposites: Fire <-> Ice.
- Adjacency ring: Fire-Air-Water-Ice-Earth (wrap).
- `STRONG = 0.20`, `ADJ = STRONG/2`, `NEUTRAL = 0.0`.
- Opposites-cancel override: if attacker element is opposite defender weapon element, interaction is neutral.
- Ice defensive bias vs Fire is defensive-only additive resistance.

## Resistance stacking
`base = armor + traits + buffs (+defensive nuance)`

`scaled = base * resistMultiplier[element]`

`clamped = clamp(scaled, resistFloor, resistCap)`

Boss affixes like `Ward(Fire)x2`, `MythicShellx3` are represented by multipliers.

## Immunity separation
- Damage immunity blocks damage numbers only.
- Effect immunity blocks categories/tags.
- Delivery blocking blocks the mechanism (GAS/SOUND/etc).

## Stall breaker
Expose/Break stacks can trigger a temporary immunity crack or resist-cap reduction to resolve 0-damage loops.
