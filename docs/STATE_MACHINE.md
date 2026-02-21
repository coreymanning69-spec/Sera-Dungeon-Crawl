# State Machine

Primary run flow:

`Title -> RunSetup -> FightIntro -> Fight -> FightResult -> Regear -> NextFight ... -> RunEnd`

Autobattle-specific notes:

- Auto/manual toggle is legal only during `Fight`.
- Save/Load is legal only in `Regear` (between fights).
- Load never restores an in-progress turn branch.
- Overlay/menu routes can always return to Title with confirmation.
