# State Machine

Primary flow:

`Title -> RunSetup -> FightIntro -> Fight -> FightResult -> Regear -> NextFight -> FightIntro ... -> RunEnd`

Operational constraints:
- Save/Load is only legal in `Regear` / between-fight states.
- Load restores between-fights progression, never an in-progress turn branch.
- Menu overlay can always route back to Title with confirmation.
