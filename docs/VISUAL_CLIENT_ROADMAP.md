# Visual Client Roadmap

The Python simulation remains authoritative. A future browser client should replay
structured combat, training, and shrine-defense summaries before it attempts to
own interactive rules.

## Target Stack

- TypeScript + Vite for the application shell.
- Phaser for 2D combat scenes, shrine-defense lanes, sprite animation, hit FX,
  portraits, and lightweight camera movement.
- DOM overlays for setup menus, training results, analytics, inventory, and
  other text-heavy surfaces.

## Data Contract

- Python exports scenario specs and run summaries as JSON.
- The browser client treats those exports as replay data, not source-of-truth
  game state.
- Asset lookup should use manifest keys such as `enemy.wailing_phantom`,
  `weapon.iron_claymore`, `fx.divine_hit`, and `portrait.sera_idle`.

## First Milestones

1. Render a Training Grounds result as a readable animated replay.
2. Render Shrine Defense waves with base sprites, troops, turrets, enemy lanes, leaks, and core HP.
3. Add a browser setup UI that writes scenario-spec JSON for Python to execute.
4. Only port simulation rules after the JSON contract and replay UI are stable.
