#!/usr/bin/env python3
"""
SERA: ENDLESS ENGAGEMENT — Combat Simulation Demo

Runs 3 scripted combat scenarios showing the math engine in action.

Scenario 1: "The Setup" — Petty Shiv vs Flickering Imps (multi-kill overkill)
Scenario 2: "The Permission Problem" — Wrong weapon vs Ghost, then crafted fix
Scenario 3: "The Boss Fight" — Full build vs Dreadknight (all systems firing)
"""

from sera.tags import DamageTag
from sera.weapon import Weapon, Affix
from sera.enemy import Enemy, EnemyAbility, AnnoyanceType, EnemyVulnerability
from sera.interest import InterestManager
from sera.combat import resolve_combat
from sera.crafting import CRAFTING_MATERIALS, apply_material
from sera.status import StatusEffect, StatusInstance


def banner(text: str) -> str:
    width = 60
    return f"\n{'#' * width}\n#  {text.center(width - 6)}  #\n{'#' * width}"


def run_scenario_1():
    """The Setup: Petty Shiv vs 2 Flickering Imps. Showcases overkill + multi-kill."""
    print(banner("SCENARIO 1: THE SETUP"))
    print('  "Two imps. One shiv. This won\'t take long."')

    # Build weapon: Petty Rusty Shiv of Agony
    weapon = Weapon(
        name="Rusty Shiv",
        base_damage=1,
        tags=[DamageTag.PHYSICAL, DamageTag.BLEED],
        prefix=Affix(
            name="Petty",
            description="Hits harder when they're at full HP.",
            affix_type="prefix",
            flat_bonus=2,
            flat_condition="enemy_full_hp",
        ),
        suffix=Affix(
            name="of Agony",
            description="Every debuff is another reason to hurt.",
            affix_type="suffix",
            per_stack_bonus=1,
            per_stack_source="debuffs_on_target",
        ),
        set_bonus=Affix(
            name="Drama Queen",
            description="+1 per debuff. Sera rewards suffering.",
            affix_type="set_bonus",
            per_stack_bonus=1,
            per_stack_source="debuffs_on_target",
        ),
    )

    # Build enemies: 2 imps, low HP for overkill demo
    imp1 = Enemy(
        name="Imp Alpha",
        max_hp=8,
        archetype="trash",
        abilities=[
            EnemyAbility("Scratch", AnnoyanceType.WEAK_HIT, flavor="It scratches. How original."),
        ],
        flavor="Small. Pointless. About to be dead.",
    )
    imp2 = Enemy(
        name="Imp Beta",
        max_hp=8,
        archetype="trash",
        abilities=[
            EnemyAbility("Scratch", AnnoyanceType.WEAK_HIT, flavor="The other one scratches too."),
        ],
        flavor="Backup. There is no backup.",
    )

    # Pre-apply debuffs to Imp Alpha for the Agony/Drama Queen showcase
    imp1.apply_status(StatusEffect.BLEEDING, duration=5)
    imp1.apply_status(StatusEffect.BURNING, duration=5)
    imp1.apply_status(StatusEffect.CORRODED, duration=5)

    interest = InterestManager(current_patience=85)

    print(f"\n  Weapon: {weapon}")
    print(f"  Imp Alpha has {len(imp1.statuses)} debuffs pre-applied (Bleed, Burn, Corrode)")
    print(f"  Imp Alpha HP: {imp1.max_hp}  |  Imp Beta HP: {imp2.max_hp}")
    print(f"  Starting Patience: {interest.current_patience}")

    result = resolve_combat(weapon, [imp1, imp2], interest, max_turns=3)
    for line in result.log:
        print(line)

    print(f"\n  Result: {result.enemies_killed} kills, "
          f"{result.patience_remaining} Patience remaining, "
          f"{'GAME OVER' if result.game_over else 'Sera continues.'}")


def run_scenario_2():
    """The Permission Problem: Iron Sword vs Ghost (fails), then crafted fix."""
    print(banner("SCENARIO 2: THE PERMISSION PROBLEM"))
    print('  "A ghost. And I brought... a sword. A PHYSICAL sword."')
    print('  "This is YOUR fault."')

    # Weapon WITHOUT divine/ethereal tag
    sword = Weapon(
        name="Iron Sword",
        base_damage=3,
        tags=[DamageTag.PHYSICAL, DamageTag.HEAVY],
        flavor="A fine weapon. Against the wrong enemy.",
    )

    ghost = Enemy(
        name="Wailing Phantom",
        max_hp=25,
        archetype="elite",
        vulnerability=EnemyVulnerability.REQUIRES_DIVINE_OR_ETHEREAL,
        abilities=[
            EnemyAbility("Ethereal Wail", AnnoyanceType.WEAK_HIT, flavor="It screams. Poorly."),
        ],
        flavor="Immune to the mundane. Like Sera, actually.",
    )

    interest = InterestManager(current_patience=70)

    print(f"\n  --- ATTEMPT 1: Wrong weapon ---")
    print(f"  Weapon: {sword}")
    print(f"  Ghost requires: [DIVINE] or [ETHEREAL] (immune to mundane steel)")
    print(f"  Sword has: [{', '.join(t.name for t in sword.all_tags)}]")

    result1 = resolve_combat(sword, [ghost], interest, max_turns=2)
    for line in result1.log:
        print(line)

    # Now craft the fix
    print(banner("CRAFTING INTERLUDE"))
    print('  Sera finds a Moonstone.')
    print('  "Finally. Let me fix this embarrassment."')

    craft_log = apply_material(sword, CRAFTING_MATERIALS["Moonstone"])
    for line in craft_log:
        print(line)

    # Reset ghost for round 2
    ghost2 = Enemy(
        name="Wailing Phantom",
        max_hp=25,
        archetype="elite",
        vulnerability=EnemyVulnerability.REQUIRES_DIVINE_OR_ETHEREAL,
        abilities=[
            EnemyAbility("Ethereal Wail", AnnoyanceType.WEAK_HIT, flavor="It screams. Again."),
        ],
    )

    # Add a suffix for extra punch
    sword.suffix = Affix(
        name="of the First Strike",
        description="+5 on the opening hit.",
        affix_type="suffix",
        flat_bonus=5,
        flat_condition="first_hit",
        inflicts_status="MARKED",
        status_duration=3,
    )

    print(f"\n  --- ATTEMPT 2: Correct weapon ---")
    print(f"  Weapon: {sword}")
    print(f"  Tags: [{', '.join(t.name for t in sword.all_tags)}]")

    result2 = resolve_combat(sword, [ghost2], interest, max_turns=3)
    for line in result2.log:
        print(line)


def run_scenario_3():
    """The Boss Fight: Full build vs Dreadknight. All systems active."""
    print(banner("SCENARIO 3: THE BOSS FIGHT"))
    print('  "50 HP. 5 Armor. A monologue. Let\'s see if it lasts 5 turns."')

    # Full build weapon
    weapon = Weapon(
        name="War Maul",
        base_damage=3,
        tags=[DamageTag.PHYSICAL, DamageTag.HEAVY],
        prefix=Affix(
            name="Cruel",
            description="Kicks them when they're down.",
            affix_type="prefix",
            flat_bonus=3,
            flat_condition="enemy_below_half",
        ),
        suffix=Affix(
            name="of Execution",
            description="x2 below half HP. Finish it.",
            affix_type="suffix",
            multiplier=2.0,
            mult_condition="enemy_below_half",
            inflicts_status="BLEEDING",
            status_duration=3,
        ),
        set_bonus=Affix(
            name="Drama Queen",
            description="+1 per debuff on target.",
            affix_type="set_bonus",
            per_stack_bonus=1,
            per_stack_source="debuffs_on_target",
        ),
        flavor='"Heavy. Mean. Perfect."',
    )

    boss = Enemy(
        name="Clanking Dreadknight",
        max_hp=50,
        archetype="boss",
        vulnerability=EnemyVulnerability.REQUIRES_HEAVY,
        armor=5,
        abilities=[
            EnemyAbility("Shield Bash", AnnoyanceType.STUN, cooldown=4,
                         flavor="It tries to stun a Goddess. Bold."),
            EnemyAbility("Oath of Honor", AnnoyanceType.MONOLOGUE, cooldown=6,
                         charge_time=3, flavor="It begins its oath. Three turns of this."),
            EnemyAbility("Sword Swing", AnnoyanceType.WEAK_HIT,
                         flavor="Predictable."),
        ],
        flavor="50 pounds of armor. 0 grams of personality.",
    )

    interest = InterestManager(current_patience=90)

    print(f"\n  Weapon: {weapon}")
    print(f"  Boss: {boss}")
    print(f"  Starting Patience: {interest.current_patience}")
    print(f"\n  BUILD LOGIC:")
    print(f"    Base: 3 dmg")
    print(f"    Above half HP: 3 dmg - 5 armor = 0 effective. Rough start.")
    print(f"    Below half HP: (3 + 3) x 2 = 12 - 5 armor = 7. Now we're talking.")
    print(f"    With debuffs:  (3 + 3) x 2 + N = 12+N - 5 armor. It snowballs.")

    result = resolve_combat(weapon, [boss], interest, max_turns=3)
    for line in result.log:
        print(line)

    print(f"\n  After 3 turns: {result.enemies_killed} kills, {result.patience_remaining} Patience remaining.")
    print(f"  {'GAME OVER' if result.game_over else 'The fight continues — armor was eating everything above half HP.'}")


def run_scenario_4():
    """Elemental Counterplay: Inferno Pike vs Rimebound Golem. Fire melts ice."""
    print(banner("SCENARIO 4: ELEMENTAL COUNTERPLAY"))
    print('  "A glacier with arms. Let me show it what fire does."')

    weapon = Weapon(
        name="Inferno Pike",
        base_damage=3,
        tags=[DamageTag.FIRE, DamageTag.HEAVY],
        prefix=Affix(
            name="Blazing",
            description="Everything burns eventually. Grants Fire.",
            affix_type="prefix",
            flat_bonus=1,
            flat_condition="always",
            multiplier=1.5,
            mult_condition="enemy_has_debuffs",
            granted_tag=DamageTag.FIRE,
            inflicts_status="BURNING",
            status_duration=2,
            status_potency=1,
        ),
        suffix=Affix(
            name="of Kindling",
            description="Casting targets ignite beautifully.",
            affix_type="suffix",
            multiplier=2.0,
            mult_condition="enemy_casting",
            inflicts_status="BURNING",
            status_duration=3,
            status_potency=1,
        ),
        flavor='"A spear of spite and open flame."',
    )

    golem = Enemy(
        name="Rimebound Golem",
        max_hp=34,
        archetype="elite",
        vulnerability=EnemyVulnerability.REQUIRES_HEAVY,
        armor=3,
        elemental_weaknesses=[DamageTag.FIRE],
        elemental_resistances=[DamageTag.ICE],
        abilities=[
            EnemyAbility("Permafrost Slam", AnnoyanceType.STUN, cooldown=4,
                         flavor="It swings an iceberg. Groundbreaking."),
            EnemyAbility("Cold Shoulder", AnnoyanceType.WEAK_HIT,
                         flavor="A glacial jab. Emotionally accurate."),
        ],
        flavor="A walking glacier with posture issues.",
    )

    interest = InterestManager(current_patience=80)

    print(f"\n  Weapon: {weapon}")
    print(f"  Enemy:  {golem}")
    print(f"  Starting Patience: {interest.current_patience}")
    print(f"\n  ELEMENTAL MATCHUP:")
    print(f"    Golem is WEAK to FIRE → +2 bonus damage per hit")
    print(f"    Golem RESISTS ICE → -1 penalty (not relevant here)")
    print(f"    Blazing prefix inflicts BURNING → enables x1.5 multiplier next hit")
    print(f"    Pike has HEAVY tag → passes vulnerability gate")

    result = resolve_combat(weapon, [golem], interest, max_turns=4)
    for line in result.log:
        print(line)

    print(f"\n  After 4 turns: {result.enemies_killed} kill(s). Patience: {result.patience_remaining}/{interest.max_patience}")
    print(f"  {'GAME OVER' if result.game_over else 'Fire wins. Obviously.'}")


def main():
    print(banner("SERA: ENDLESS ENGAGEMENT"))
    print('  "I am a Goddess. Entertain me or I leave."')
    print("  A Systems-Heavy Roguelike Prototype")
    print(f"  {'─' * 40}")
    print("  Core Loop: Kill aggressively to stay interested.")
    print("  Lose State: Patience hits 0. Sera leaves. Game Over.")
    print("  Scale: 1-30 damage. Build the machine, not the number.")

    run_scenario_1()
    print("\n" + "─" * 60)
    run_scenario_2()
    print("\n" + "─" * 60)
    run_scenario_3()
    print("\n" + "─" * 60)
    run_scenario_4()

    print(banner("END OF SIMULATION"))
    print('  Sera: "Not bad. Not GOOD, but not bad."')
    print('  "Build more. I might stay."')


if __name__ == "__main__":
    main()
