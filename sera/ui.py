"""
Text-block UI renderer for SERA: ENDLESS ENGAGEMENT.

All display is box-drawn with simple ASCII blocks.
Numbers for input. Monospace assumed.
"""

from __future__ import annotations
import os

from sera.weapon import Weapon
from sera.enemy import Enemy, ANNOYANCE_COST
from sera.interest import InterestManager
from sera.crafting import CraftingMaterial


# ─────────────────────────────────────────────────────────
# Drawing primitives
# ─────────────────────────────────────────────────────────

W = 60  # standard box width


def clear():
    if os.environ.get("TERM"):
        os.system("cls" if os.name == "nt" else "clear")
    else:
        print("\n" * 2)


def box_top():
    return "+" + "-" * (W - 2) + "+"


def box_bot():
    return box_top()


def box_line(text: str, align: str = "left") -> str:
    inner = W - 4  # 2 for borders, 2 for padding
    if align == "center":
        content = text.center(inner)
    elif align == "right":
        content = text.rjust(inner)
    else:
        content = text.ljust(inner)
    return f"| {content} |"


def box_blank():
    return box_line("")


def box_divider():
    return "|" + "-" * (W - 2) + "|"


def hp_bar(current: int, maximum: int, width: int = 20, fill: str = "#", empty: str = "-") -> str:
    ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
    filled = int(ratio * width)
    return f"[{fill * filled}{empty * (width - filled)}] {current}/{maximum}"


def patience_bar(interest: InterestManager) -> str:
    return hp_bar(interest.current_patience, interest.max_patience, width=20)


# ─────────────────────────────────────────────────────────
# Composite screens
# ─────────────────────────────────────────────────────────

def render_title_screen() -> str:
    lines = [
        box_top(),
        box_blank(),
        box_line("S E R A", "center"),
        box_line("ENDLESS ENGAGEMENT", "center"),
        box_blank(),
        box_divider(),
        box_line('"I am a Goddess. Entertain me."', "center"),
        box_divider(),
        box_blank(),
        box_line("[1] New Game"),
        box_line("[2] Quit"),
        box_blank(),
        box_bot(),
    ]
    return "\n".join(lines)


def render_floor_intro(floor: int, enemies: list[Enemy], interest: InterestManager) -> str:
    lines = [
        box_top(),
        box_line(f"FLOOR {floor}", "center"),
        box_divider(),
        box_line(f"Patience: {patience_bar(interest)}"),
        box_divider(),
    ]
    lines.append(box_line("ENEMIES:"))
    for i, e in enumerate(enemies):
        tag_req = e.vulnerability.name if e.vulnerability.name != "NONE" else "any"
        status = "ALIVE" if e.current_hp > 0 else "DEAD"
        lines.append(box_line(f"  [{i+1}] {e.name} ({e.archetype})"))
        lines.append(box_line(f"      HP: {hp_bar(e.current_hp, e.max_hp, 15)}"))
        if e.armor > 0:
            lines.append(box_line(f"      Armor: {e.armor}"))
        lines.append(box_line(f"      Requires: [{tag_req}]"))
        if e.statuses:
            st = ", ".join(f"{s.effect.name}({s.potency})" for s in e.statuses)
            lines.append(box_line(f"      Debuffs: {st}"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_combat_hud(
    turn: int,
    weapon: Weapon,
    enemies: list[Enemy],
    interest: InterestManager,
) -> str:
    tag_str = ", ".join(t.name for t in weapon.all_tags)
    lines = [
        box_top(),
        box_line(f"TURN {turn}", "center"),
        box_divider(),
        box_line(f"Patience: {patience_bar(interest)}"),
        box_line(f"Weapon:   {weapon.display_name} ({weapon.base_damage} dmg)"),
        box_line(f"Tags:     [{tag_str}]"),
        box_divider(),
    ]

    alive = [e for e in enemies if e.current_hp > 0]
    for i, e in enumerate(alive):
        casting = " [CASTING...]" if e.is_casting else ""
        lines.append(box_line(f"  [{i+1}] {e.name}{casting}"))
        lines.append(box_line(f"      HP: {hp_bar(e.current_hp, e.max_hp, 15)}"))
        if e.statuses:
            st = ", ".join(f"{s.effect.name}" for s in e.statuses)
            lines.append(box_line(f"      ({st})"))

    lines.append(box_divider())
    lines.append(box_line("ACTIONS:"))
    for i, e in enumerate(alive):
        lines.append(box_line(f"  [{i+1}] Attack {e.name}"))
    lines.append(box_line(f"  [I] Inspect enemy"))
    lines.append(box_line(f"  [W] View weapon details"))
    lines.append(box_blank())
    lines.append(box_bot())
    return "\n".join(lines)


def render_damage_report(steps: list[str], target_name: str, actual: int, armor_absorbed: int) -> str:
    lines = [
        box_top(),
        box_line(f"DAMAGE vs {target_name}", "center"),
        box_divider(),
    ]
    for step in steps:
        lines.append(box_line(f"  {step}"))
    if armor_absorbed > 0:
        lines.append(box_line(f"  Armor absorbs: {armor_absorbed}"))
    lines.append(box_divider())
    lines.append(box_line(f"DEALT: {actual} damage", "center"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_enemy_action(enemy: Enemy, ability_name: str, flavor: str, cost: int) -> str:
    lines = [
        box_top(),
        box_line(f"{enemy.name} acts!", "center"),
        box_divider(),
        box_line(f"  {ability_name}"),
        box_line(f'  "{flavor}"'),
        box_line(f"  [-{cost} Patience]"),
        box_bot(),
    ]
    return "\n".join(lines)


def render_kill_report(enemy_name: str, events: list[str]) -> str:
    lines = [
        box_top(),
        box_line(f"{enemy_name} DEFEATED", "center"),
        box_divider(),
    ]
    for ev in events:
        lines.append(box_line(ev.strip()))
    lines.append(box_bot())
    return "\n".join(lines)


def render_loot_screen(
    weapon_loot: Weapon | None,
    material_loot: CraftingMaterial | None,
    interest: InterestManager,
) -> str:
    lines = [
        box_top(),
        box_line("ROOM CLEARED", "center"),
        box_divider(),
        box_line(f"Patience: {patience_bar(interest)}"),
        box_divider(),
        box_line("LOOT:", "center"),
    ]
    choices = []
    idx = 1
    if weapon_loot:
        tag_str = ", ".join(t.name for t in weapon_loot.all_tags)
        lines.append(box_line(f"  [{idx}] {weapon_loot.display_name} ({weapon_loot.base_damage} dmg)"))
        lines.append(box_line(f"      [{tag_str}]"))
        if weapon_loot.prefix:
            lines.append(box_line(f"      Prefix: {weapon_loot.prefix.name} - {weapon_loot.prefix.description}"))
        if weapon_loot.suffix:
            lines.append(box_line(f"      Suffix: {weapon_loot.suffix.name} - {weapon_loot.suffix.description}"))
        if weapon_loot.flavor:
            lines.append(box_line(f'      "{weapon_loot.flavor}"'))
        choices.append(("weapon", idx))
        idx += 1

    if material_loot:
        tag_name = material_loot.grants_tag.name if material_loot.grants_tag else "???"
        lines.append(box_line(f"  [{idx}] {material_loot.name} (grants [{tag_name}])"))
        if material_loot.flavor:
            lines.append(box_line(f'      {material_loot.flavor}'))
        choices.append(("material", idx))
        idx += 1

    if not weapon_loot and not material_loot:
        lines.append(box_line('  Nothing. "Boring loot is worse than no loot."'))

    lines.append(box_blank())
    lines.append(box_bot())
    return "\n".join(lines), choices


def render_inventory(
    weapons: list[Weapon],
    materials: list[CraftingMaterial],
    equipped_idx: int,
) -> str:
    lines = [
        box_top(),
        box_line("INVENTORY", "center"),
        box_divider(),
        box_line("WEAPONS:"),
    ]
    for i, w in enumerate(weapons):
        marker = " [E]" if i == equipped_idx else ""
        tag_str = ", ".join(t.name for t in w.all_tags)
        lines.append(box_line(f"  [{i+1}] {w.display_name} ({w.base_damage} dmg){marker}"))
        lines.append(box_line(f"      [{tag_str}]"))
        if w.prefix:
            lines.append(box_line(f"      PRE: {w.prefix.name} - {w.prefix.description}"))
        if w.suffix:
            lines.append(box_line(f"      SUF: {w.suffix.name} - {w.suffix.description}"))

    lines.append(box_divider())
    lines.append(box_line("MATERIALS:"))
    if materials:
        for i, m in enumerate(materials):
            tag_name = m.grants_tag.name if m.grants_tag else "???"
            lines.append(box_line(f"  [{i+1}] {m.name} (grants [{tag_name}])"))
    else:
        lines.append(box_line("  (empty)"))

    lines.append(box_bot())
    return "\n".join(lines)


def render_equip_screen(weapons: list[Weapon], equipped_idx: int) -> str:
    lines = [
        box_top(),
        box_line("EQUIP WEAPON", "center"),
        box_divider(),
    ]
    for i, w in enumerate(weapons):
        marker = " << EQUIPPED" if i == equipped_idx else ""
        tag_str = ", ".join(t.name for t in w.all_tags)
        lines.append(box_line(f"  [{i+1}] {w.display_name} ({w.base_damage} dmg){marker}"))
        lines.append(box_line(f"      [{tag_str}]"))
    lines.append(box_blank())
    lines.append(box_line("[0] Cancel"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_craft_screen(
    weapons: list[Weapon],
    materials: list[CraftingMaterial],
    equipped_idx: int,
) -> str:
    lines = [
        box_top(),
        box_line("CRAFTING BENCH", "center"),
        box_divider(),
        box_line("Apply a material to a weapon:"),
        box_blank(),
        box_line("WEAPONS:"),
    ]
    for i, w in enumerate(weapons):
        marker = " [E]" if i == equipped_idx else ""
        tag_str = ", ".join(t.name for t in w.all_tags)
        lines.append(box_line(f"  [{i+1}] {w.display_name}{marker}"))
        lines.append(box_line(f"      [{tag_str}]"))

    lines.append(box_divider())
    lines.append(box_line("MATERIALS:"))
    for i, m in enumerate(materials):
        tag_name = m.grants_tag.name if m.grants_tag else "???"
        lines.append(box_line(f"  [{i+1}] {m.name} (grants [{tag_name}])"))

    lines.append(box_blank())
    lines.append(box_line("[0] Cancel"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_weapon_detail(weapon: Weapon) -> str:
    tag_str = ", ".join(t.name for t in weapon.all_tags)
    lines = [
        box_top(),
        box_line(f"WEAPON: {weapon.display_name}", "center"),
        box_divider(),
        box_line(f"  Base Damage: {weapon.base_damage}"),
        box_line(f"  Tags: [{tag_str}]"),
    ]
    if weapon.prefix:
        lines.append(box_divider())
        lines.append(box_line(f"  PREFIX: {weapon.prefix.name}"))
        lines.append(box_line(f"  {weapon.prefix.description}"))
        if weapon.prefix.flat_bonus:
            lines.append(box_line(f"    +{weapon.prefix.flat_bonus} (if {weapon.prefix.flat_condition})"))
        if weapon.prefix.multiplier != 1.0:
            lines.append(box_line(f"    x{weapon.prefix.multiplier} (if {weapon.prefix.mult_condition})"))
        if weapon.prefix.per_stack_bonus:
            lines.append(box_line(f"    +{weapon.prefix.per_stack_bonus}/stack ({weapon.prefix.per_stack_source})"))
        if weapon.prefix.granted_tag:
            lines.append(box_line(f"    Grants [{weapon.prefix.granted_tag.name}]"))
    if weapon.suffix:
        lines.append(box_divider())
        lines.append(box_line(f"  SUFFIX: {weapon.suffix.name}"))
        lines.append(box_line(f"  {weapon.suffix.description}"))
        if weapon.suffix.flat_bonus:
            lines.append(box_line(f"    +{weapon.suffix.flat_bonus} (if {weapon.suffix.flat_condition})"))
        if weapon.suffix.multiplier != 1.0:
            lines.append(box_line(f"    x{weapon.suffix.multiplier} (if {weapon.suffix.mult_condition})"))
        if weapon.suffix.per_stack_bonus:
            lines.append(box_line(f"    +{weapon.suffix.per_stack_bonus}/stack ({weapon.suffix.per_stack_source})"))
        if weapon.suffix.granted_tag:
            lines.append(box_line(f"    Grants [{weapon.suffix.granted_tag.name}]"))
    if weapon.set_bonus:
        lines.append(box_divider())
        lines.append(box_line(f"  SET BONUS: {weapon.set_bonus.name}"))
        lines.append(box_line(f"  {weapon.set_bonus.description}"))
    if weapon.flavor:
        lines.append(box_divider())
        lines.append(box_line(f'"{weapon.flavor}"'))
    lines.append(box_bot())
    return "\n".join(lines)


def render_between_floors(floor: int, interest: InterestManager) -> str:
    lines = [
        box_top(),
        box_line(f"FLOOR {floor} COMPLETE", "center"),
        box_divider(),
        box_line(f"Patience: {patience_bar(interest)}"),
        box_divider(),
        box_line("[1] Continue to next floor"),
        box_line("[2] Equip weapon"),
        box_line("[3] Craft (apply material to weapon)"),
        box_line("[4] View inventory"),
        box_line("[5] Quit"),
        box_blank(),
        box_bot(),
    ]
    return "\n".join(lines)


def render_game_over(interest: InterestManager) -> str:
    lines = [
        box_top(),
        box_blank(),
        box_line("G A M E   O V E R", "center"),
        box_blank(),
        box_divider(),
        box_line('Sera rolls her eyes.', "center"),
        box_line('"This is a waste of time."', "center"),
        box_line('She teleports away.', "center"),
        box_line('The dungeon collapses behind her.', "center"),
        box_divider(),
        box_blank(),
        box_line(f"Floors cleared: {interest.turn_number}"),
        box_line(f"Total kills: {interest.total_kills}"),
        box_blank(),
        box_bot(),
    ]
    return "\n".join(lines)


def render_victory(floor: int, interest: InterestManager) -> str:
    lines = [
        box_top(),
        box_blank(),
        box_line("D U N G E O N  C L E A R E D", "center"),
        box_blank(),
        box_divider(),
        box_line('"...Acceptable."', "center"),
        box_line('Sera nods once. The highest compliment.', "center"),
        box_divider(),
        box_blank(),
        box_line(f"Floors cleared: {floor}"),
        box_line(f"Total kills: {interest.total_kills}"),
        box_line(f"Patience remaining: {interest.current_patience}"),
        box_blank(),
        box_bot(),
    ]
    return "\n".join(lines)


def render_inspect(enemy: Enemy) -> str:
    lines = [
        box_top(),
        box_line(f"INSPECT: {enemy.name}", "center"),
        box_divider(),
        box_line(f"  Archetype:     {enemy.archetype}"),
        box_line(f"  HP:            {hp_bar(enemy.current_hp, enemy.max_hp, 15)}"),
        box_line(f"  Armor:         {enemy.armor}"),
        box_line(f"  Regen/turn:    {enemy.regen_per_turn}"),
    ]
    req = enemy.vulnerability.name if enemy.vulnerability.name != "NONE" else "NONE (any weapon works)"
    lines.append(box_line(f"  Requires tag:  [{req}]"))
    if enemy.statuses:
        st = ", ".join(f"{s.effect.name}(p:{s.potency} t:{s.duration})" for s in enemy.statuses)
        lines.append(box_line(f"  Debuffs:       {st}"))
    if enemy.is_casting:
        lines.append(box_line(f"  CASTING:       {enemy.pending_ability.name} ({enemy.cast_turns_remaining}t)"))
    lines.append(box_divider())
    lines.append(box_line("Abilities:"))
    for ab in enemy.abilities:
        cost = ANNOYANCE_COST[ab.annoyance]
        lines.append(box_line(f"  {ab.name} (-{cost} PP, {ab.annoyance.name})"))
        if ab.flavor:
            lines.append(box_line(f'    "{ab.flavor}"'))
    if enemy.flavor:
        lines.append(box_divider())
        lines.append(box_line(f'"{enemy.flavor}"'))
    lines.append(box_bot())
    return "\n".join(lines)


def get_input(prompt: str = "> ") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return "quit"
