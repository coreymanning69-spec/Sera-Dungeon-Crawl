from sera.revision_110 import (
    ADJ,
    STRONG,
    DefenseProfile,
    DeliveryType,
    EffectSpec,
    EffectType,
    ExposeState,
    apply_damage_and_effect,
    apply_expose_break,
    element_interaction_modifier,
    resolve_resistance,
)


def test_opposites_cancel_logged():
    mod, cancelled, relation = element_interaction_modifier("Ice", "Fire", "Fire")
    assert mod == 0.0
    assert cancelled is True
    assert relation == "opposites-cancel"


def test_adjacent_half_magnitude():
    mod, cancelled, relation = element_interaction_modifier("Fire", "Air", None)
    assert cancelled is False
    assert relation == "adjacent"
    assert mod == ADJ
    assert ADJ == STRONG / 2


def test_ice_defensive_bias_vs_fire():
    ice = DefenseProfile(armor_element="Ice", armor_resist={"Fire": 0.10})
    water = DefenseProfile(armor_element="Water", armor_resist={"Fire": 0.10})
    ice_resist, _ = resolve_resistance(ice, "Fire")
    water_resist, _ = resolve_resistance(water, "Fire")
    assert ice_resist > water_resist


def test_damage_immune_but_gas_blind_applies():
    defense = DefenseProfile(immune_damage_types={"Divine"})
    effect = EffectSpec(tag="BLIND", effect_type=EffectType.CONTROL, delivery_type=DeliveryType.GAS, duration=2)
    out = apply_damage_and_effect(10, "Divine", "Fire", "Fire", effect, defense)
    assert out["final_damage"] == 0
    assert out["effect_result"] == "applied"


def test_boss_resist_multiplier_and_cap_clamp():
    defense = DefenseProfile(
        armor_resist={"Fire": 0.40},
        resist_multiplier={"Fire": 3.0},
        resist_cap=0.90,
    )
    _, meta = resolve_resistance(defense, "Fire")
    assert round(meta["scaled_resist"], 4) == 1.2
    assert meta["clamped"] == 0.9
    assert meta["was_clamped"] is True


def test_stall_breaker_expose_break_triggers():
    expose = ExposeState()
    triggered = False
    for _ in range(3):
        expose, triggered = apply_expose_break(expose, threshold=3, turns=2)
    assert triggered is True
    assert expose.active_turns == 2
