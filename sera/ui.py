"""
Pixel Art UI renderer for SERA: ENDLESS ENGAGEMENT.

Old-school 64/128-bit retro aesthetic using Unicode block
characters (░▒▓█▀▄▐▌) and box-drawing (╔╗╚╝║═).
Monospace terminal assumed.
"""

from __future__ import annotations
import os

from sera.weapon import Weapon
from sera.enemy import Enemy, ANNOYANCE_COST
from sera.interest import InterestManager
from sera.crafting import CraftingMaterial
from sera.equipment import EquipmentItem, EquipmentLoadout, SLOT_ORDER
from sera.stats import PlayerStats
from sera import sprites


# ─────────────────────────────────────────────────────────
# Drawing primitives — retro pixel style
# ─────────────────────────────────────────────────────────

W = 60  # standard box width


def clear():
    if os.environ.get("TERM"):
        os.system("cls" if os.name == "nt" else "clear")
    else:
        print("\n" * 2)


def box_top():
    return "╔" + "═" * (W - 2) + "╗"


def box_bot():
    return "╚" + "═" * (W - 2) + "╝"


def box_line(text: str, align: str = "left") -> str:
    inner = W - 4  # 2 for borders, 2 for padding
    if align == "center":
        content = text.center(inner)
    elif align == "right":
        content = text.rjust(inner)
    else:
        content = text.ljust(inner)
    return f"║ {content} ║"


def box_blank():
    return box_line("")


def box_divider():
    return "╠" + "═" * (W - 2) + "╣"


def box_divider_thin():
    return "║" + "─" * (W - 2) + "║"


def box_divider_pixel():
    """A decorative pixel-art divider."""
    pattern = "░▒▓█▓▒░"
    repeats = (W - 2) // len(pattern)
    remainder = (W - 2) % len(pattern)
    inner = (pattern * repeats) + pattern[:remainder]
    return "║" + inner + "║"


def box_header(text: str) -> str:
    """A highlighted header line with pixel accents."""
    inner = W - 4
    padded = f" ▓▓ {text} ▓▓ "
    return f"║ {padded.center(inner)} ║"


# ─────────────────────────────────────────────────────────
# Bars — pixel-art styled
# ─────────────────────────────────────────────────────────

def hp_bar(current: int, maximum: int, width: int = 20) -> str:
    """Pixel-art HP bar using block characters."""
    ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
    filled = int(ratio * width)
    half = 1 if (ratio * width - filled) >= 0.5 and filled < width else 0

    if ratio > 0.6:
        fill_char = "█"
        half_char = "▓"
    elif ratio > 0.3:
        fill_char = "▓"
        half_char = "▒"
    else:
        fill_char = "▒"
        half_char = "░"

    empty_char = "░"
    bar = fill_char * filled + half_char * half + empty_char * (width - filled - half)
    return f"[{bar}] {current}/{maximum}"


def patience_bar(interest: InterestManager) -> str:
    """Patience bar with mood indicator."""
    bar = hp_bar(interest.current_patience, interest.max_patience, width=18)
    pct = interest.current_patience / interest.max_patience if interest.max_patience > 0 else 0
    mood = sprites.get_mood(pct)
    p = interest.current_patience
    if p <= 15:
        return f"{bar} {mood} !! CRITICAL !!"
    if p <= 30:
        return f"{bar} {mood} ! LOW !"
    return f"{bar} {mood}"


def xp_bar(current: int, maximum: int, width: int = 15) -> str:
    """Small XP/progress bar."""
    ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
    filled = int(ratio * width)
    return f"<{'▓' * filled}{'░' * (width - filled)}>"


# ─────────────────────────────────────────────────────────
# Composite screens
# ─────────────────────────────────────────────────────────

def render_title_screen() -> str:
    lines = [
        box_top(),
        box_blank(),
    ]
    # Add the pixel art logo
    for logo_line in sprites.SERA_LOGO.strip().split("\n"):
        lines.append(box_line(logo_line, "center"))
    lines.append(box_blank())
    for sub_line in sprites.SUBTITLE_ART.strip().split("\n"):
        lines.append(box_line(sub_line, "center"))
    lines.append(box_blank())
    lines.append(box_divider_pixel())
    lines.append(box_blank())
    # Mini Sera portrait
    for portrait_line in sprites.SERA_IDLE.strip().split("\n"):
        lines.append(box_line(portrait_line, "center"))
    lines.append(box_blank())
    lines.append(box_divider())
    lines.append(box_line('"I am a Goddess. Entertain me."', "center"))
    lines.append(box_divider())
    lines.append(box_blank())
    lines.append(box_line("  ▸ [1] New Game"))
    lines.append(box_line("  ▸ [2] Quit"))
    lines.append(box_blank())
    lines.append(box_divider_pixel())
    lines.append(box_bot())
    return "\n".join(lines)


def render_floor_intro(floor: int, enemies: list[Enemy], interest: InterestManager) -> str:
    floor_label = f"░▒▓█  FLOOR {floor}  █▓▒░"
    lines = [
        box_top(),
        box_blank(),
        box_line(floor_label, "center"),
        box_blank(),
        box_divider(),
        box_line(f"Patience: {patience_bar(interest)}"),
        box_divider(),
    ]
    # Dungeon entrance art for floor 1
    if floor == 1:
        for art_line in sprites.DUNGEON_ENTRANCE.strip().split("\n"):
            lines.append(box_line(art_line, "center"))
        lines.append(box_divider_thin())

    lines.append(box_header("ENEMIES"))
    lines.append(box_blank())
    for i, e in enumerate(enemies):
        tag_req = e.vulnerability.name if e.vulnerability.name != "NONE" else "any"
        # Show mini sprite inline
        sprite_lines = sprites.get_enemy_sprite(e.archetype).strip().split("\n")
        # Just show first 3 lines of sprite as a preview
        for sl in sprite_lines[:3]:
            lines.append(box_line(f"  {sl}"))
        lines.append(box_line(f"  [{i+1}] {e.name} ({e.archetype})"))
        lines.append(box_line(f"      HP: {hp_bar(e.current_hp, e.max_hp, 15)}"))
        if e.armor > 0:
            lines.append(box_line(f"      Armor: {'▓' * e.armor}  ({e.armor})"))
        lines.append(box_line(f"      Requires: [{tag_req}]"))
        if e.statuses:
            st = ", ".join(f"{s.effect.name}({s.potency})" for s in e.statuses)
            lines.append(box_line(f"      Debuffs: {st}"))
        if i < len(enemies) - 1:
            lines.append(box_divider_thin())
    lines.append(box_blank())
    lines.append(box_bot())
    return "\n".join(lines)


def render_combat_hud(
    turn: int,
    weapon: Weapon,
    enemies: list[Enemy],
    interest: InterestManager,
    stats: PlayerStats,
    healing_charges: int,
) -> str:
    tag_str = ", ".join(t.name for t in weapon.all_tags)
    turn_label = f"╍╍╍ TURN {turn} ╍╍╍"
    lines = [
        box_top(),
        box_line(turn_label, "center"),
        box_divider(),
        box_line(f"  Patience: {patience_bar(interest)}"),
        box_divider_thin(),
        box_line(f"  ⚔ {weapon.display_name} ({weapon.base_damage} dmg)"),
        box_line(f"    Tags: [{tag_str}]"),
        box_line(f"  Flask Charges: {healing_charges}  |  AP bonus: +{stats.attack_bonus()}"),
        box_divider(),
    ]

    alive = [e for e in enemies if e.current_hp > 0]
    for i, e in enumerate(alive):
        casting = " ░░ CASTING ░░" if e.is_casting else ""
        req = e.vulnerability.name.replace("REQUIRES_", "") if e.vulnerability.name != "NONE" else ""
        tag_hint = f" (needs [{req}])" if req else ""

        # Enemy display with mini archetype icon
        icon = "◆" if e.archetype == "boss" else "◇" if e.archetype == "elite" else "·"
        lines.append(box_line(f"  {icon} [{i+1}] {e.name}{casting}{tag_hint}"))
        lines.append(box_line(f"        HP: {hp_bar(e.current_hp, e.max_hp, 15)}"))
        if e.armor > 0:
            lines.append(box_line(f"        Armor: {'▓' * min(e.armor, 10)} ({e.armor})"))
        if e.statuses:
            st = ", ".join(f"{s.effect.name}({s.potency})" for s in e.statuses)
            lines.append(box_line(f"        [{st}]"))

    lines.append(box_divider())
    lines.append(box_header("ACTIONS"))
    for i, e in enumerate(alive):
        lines.append(box_line(f"  ▸ [{i+1}] Attack {e.name}"))
    lines.append(box_line(f"  ▸ [I] Inspect enemy"))
    lines.append(box_line(f"  ▸ [W] View weapon details"))
    lines.append(box_line(f"  ▸ [H] Use healing flask"))
    lines.append(box_blank())
    lines.append(box_bot())
    return "\n".join(lines)


def render_damage_report(steps: list[str], target_name: str, actual: int, armor_absorbed: int) -> str:
    lines = [
        box_top(),
    ]
    # Show hit effect art
    for art_line in sprites.HIT_EFFECT.strip().split("\n"):
        lines.append(box_line(art_line, "center"))
    lines.append(box_line(f"DAMAGE vs {target_name}", "center"))
    lines.append(box_divider())
    for step in steps:
        lines.append(box_line(f"  {step}"))
    if armor_absorbed > 0:
        lines.append(box_line(f"  Armor absorbs: {armor_absorbed}"))
    lines.append(box_divider_pixel())
    lines.append(box_line(f"▓▓ DEALT: {actual} damage ▓▓", "center"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_enemy_action(enemy: Enemy, ability_name: str, flavor: str, cost: int) -> str:
    lines = [
        box_top(),
        box_line(f"░░ {enemy.name} acts! ░░", "center"),
        box_divider(),
    ]
    # Show a couple lines of enemy sprite
    sprite_lines = sprites.get_enemy_sprite(enemy.archetype).strip().split("\n")
    for sl in sprite_lines[:4]:
        lines.append(box_line(sl, "center"))
    lines.append(box_divider_thin())
    lines.append(box_line(f"  ▸ {ability_name}"))
    lines.append(box_line(f'  "{flavor}"'))
    lines.append(box_line(f"  [-{cost} Patience]"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_kill_report(enemy_name: str, events: list[str]) -> str:
    lines = [
        box_top(),
    ]
    for art_line in sprites.SKULL.strip().split("\n"):
        lines.append(box_line(art_line, "center"))
    lines.append(box_line(f"▓▓ {enemy_name} DEFEATED ▓▓", "center"))
    lines.append(box_divider())
    for ev in events:
        lines.append(box_line(ev.strip()))
    lines.append(box_bot())
    return "\n".join(lines)


def render_loot_screen(
    weapon_loot: Weapon | None,
    material_loot: CraftingMaterial | None,
    interest: InterestManager,
    shard_drop: int = 0,
) -> str:
    lines = [
        box_top(),
        box_line("░▒▓█ ROOM CLEARED █▓▒░", "center"),
        box_divider(),
        box_line(f"Patience: {patience_bar(interest)}"),
        box_divider(),
    ]
    # Treasure art
    for art_line in sprites.TREASURE.strip().split("\n"):
        lines.append(box_line(art_line, "center"))
    lines.append(box_blank())
    lines.append(box_header("LOOT"))
    lines.append(box_blank())

    if shard_drop > 0:
        for sl in sprites.SHARD.strip().split("\n"):
            lines.append(box_line(f"    {sl}"))
        lines.append(box_line(f"  ◇ {shard_drop} Upgrade Shard{'s' if shard_drop != 1 else ''} (auto-collected)"))
        lines.append(box_blank())

    choices = []
    idx = 1
    if weapon_loot:
        tag_str = ", ".join(t.name for t in weapon_loot.all_tags)
        # Show weapon sprite
        sprite = sprites.get_weapon_sprite(weapon_loot.name)
        for sl in sprite.strip().split("\n")[:3]:
            lines.append(box_line(f"    {sl}"))
        lines.append(box_line(f"  ▸ [{idx}] {weapon_loot.display_name} ({weapon_loot.base_damage} dmg)"))
        lines.append(box_line(f"        [{tag_str}]"))
        if weapon_loot.prefix:
            lines.append(box_line(f"        Prefix: {weapon_loot.prefix.name}"))
        if weapon_loot.suffix:
            lines.append(box_line(f"        Suffix: {weapon_loot.suffix.name}"))
        if weapon_loot.flavor:
            lines.append(box_line(f'        "{weapon_loot.flavor}"'))
        choices.append(("weapon", idx))
        idx += 1

    if material_loot:
        tag_name = material_loot.grants_tag.name if material_loot.grants_tag else "???"
        lines.append(box_line(f"  ▸ [{idx}] {material_loot.name} (grants [{tag_name}])"))
        if material_loot.flavor:
            lines.append(box_line(f'        {material_loot.flavor}'))
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
    upgrade_shards: int = 0,
    equipment_items: list[EquipmentItem] | None = None,
    stats: PlayerStats | None = None,
) -> str:
    lines = [
        box_top(),
        box_line("░▒▓█ INVENTORY █▓▒░", "center"),
        box_divider(),
        box_header("WEAPONS"),
    ]
    for i, w in enumerate(weapons):
        marker = " ◄ EQUIPPED" if i == equipped_idx else ""
        tag_str = ", ".join(t.name for t in w.all_tags)
        upgrade_display = f" [{sprites.get_upgrade_display(w.upgrade_level)}]" if w.upgrade_level > 0 else ""
        lines.append(box_line(f"  ▸ [{i+1}] {w.display_name} ({w.effective_base_damage} dmg){marker}{upgrade_display}"))
        lines.append(box_line(f"        [{tag_str}]"))
        if w.prefix:
            lines.append(box_line(f"        PRE: {w.prefix.name} - {w.prefix.description}"))
        if w.suffix:
            lines.append(box_line(f"        SUF: {w.suffix.name} - {w.suffix.description}"))

    lines.append(box_divider())
    lines.append(box_header("MATERIALS"))
    if materials:
        for i, m in enumerate(materials):
            tag_name = m.grants_tag.name if m.grants_tag else "???"
            lines.append(box_line(f"  ▸ [{i+1}] {m.name} (grants [{tag_name}])"))
    else:
        lines.append(box_line("  (empty)"))

    lines.append(box_divider())
    lines.append(box_header("EQUIPMENT STASH"))
    if equipment_items:
        for i, item in enumerate(equipment_items):
            lines.append(box_line(f"  ▸ [{i+1}] {item.name} ({item.slot}) {item.ascii_art}"))
    else:
        lines.append(box_line("  (empty)"))

    lines.append(box_divider())
    lines.append(box_line(f"  ◇ Upgrade Shards: {upgrade_shards}"))
    if stats:
        lines.append(box_line("  Stats: " + " | ".join(stats.as_lines())))

    lines.append(box_blank())
    lines.append(box_bot())
    return "\n".join(lines)


def render_equip_screen(weapons: list[Weapon], equipped_idx: int) -> str:
    lines = [
        box_top(),
        box_line("░▒▓█ EQUIP WEAPON █▓▒░", "center"),
        box_divider(),
    ]
    for i, w in enumerate(weapons):
        marker = " ◄◄ EQUIPPED" if i == equipped_idx else ""
        tag_str = ", ".join(t.name for t in w.all_tags)
        # Show weapon sprite preview
        sprite = sprites.get_weapon_sprite(w.name)
        for sl in sprite.strip().split("\n")[:2]:
            lines.append(box_line(f"    {sl}"))
        lines.append(box_line(f"  ▸ [{i+1}] {w.display_name} ({w.base_damage} dmg){marker}"))
        lines.append(box_line(f"        [{tag_str}]"))
        if i < len(weapons) - 1:
            lines.append(box_divider_thin())
    lines.append(box_blank())
    lines.append(box_line("  ▸ [0] Cancel"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_craft_screen(
    weapons: list[Weapon],
    materials: list[CraftingMaterial],
    equipped_idx: int,
) -> str:
    lines = [
        box_top(),
        box_line("░▒▓█ CRAFTING BENCH █▓▒░", "center"),
        box_divider(),
        box_line("Apply a material to a weapon:"),
        box_blank(),
        box_header("WEAPONS"),
    ]
    for i, w in enumerate(weapons):
        marker = " ◄" if i == equipped_idx else ""
        tag_str = ", ".join(t.name for t in w.all_tags)
        lines.append(box_line(f"  ▸ [{i+1}] {w.display_name}{marker}"))
        lines.append(box_line(f"        [{tag_str}]"))

    lines.append(box_divider())
    lines.append(box_header("MATERIALS"))
    for i, m in enumerate(materials):
        tag_name = m.grants_tag.name if m.grants_tag else "???"
        lines.append(box_line(f"  ▸ [{i+1}] {m.name} (grants [{tag_name}])"))

    lines.append(box_blank())
    lines.append(box_line("  ▸ [0] Cancel"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_upgrade_screen(
    weapons: list[Weapon],
    equipped_idx: int,
    shards: int,
) -> str:
    lines = [
        box_top(),
        box_line("░▒▓█ UPGRADE WEAPON █▓▒░", "center"),
        box_divider(),
    ]
    # Anvil art
    for sl in sprites.UPGRADE_ANVIL.strip().split("\n"):
        lines.append(box_line(sl, "center"))
    lines.append(box_divider_thin())
    lines.append(box_line(f"  ◇ Shards available: {shards}"))
    lines.append(box_divider())
    lines.append(box_header("WEAPONS"))
    for i, w in enumerate(weapons):
        marker = " ◄" if i == equipped_idx else ""
        lvl = sprites.get_upgrade_display(w.upgrade_level)
        if w.can_upgrade:
            cost = w.upgrade_cost
            lines.append(box_line(f"  ▸ [{i+1}] {w.display_name} [{lvl}]{marker}"))
            lines.append(box_line(f"        Dmg: {w.effective_base_damage}  |  Next: {cost} shard{'s' if cost != 1 else ''}"))
        else:
            lines.append(box_line(f"  ▸ [{i+1}] {w.display_name} [{lvl}] MAX{marker}"))
            lines.append(box_line(f"        Dmg: {w.effective_base_damage}  |  Fully upgraded"))

    lines.append(box_blank())
    lines.append(box_line("  ▸ [0] Cancel"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_weapon_detail(weapon: Weapon) -> str:
    tag_str = ", ".join(t.name for t in weapon.all_tags)
    lines = [
        box_top(),
        box_line(f"░▒▓ WEAPON: {weapon.display_name} ▓▒░", "center"),
        box_divider(),
    ]
    # Show weapon sprite
    sprite = sprites.get_weapon_sprite(weapon.name)
    for sl in sprite.strip().split("\n"):
        lines.append(box_line(sl, "center"))
    lines.append(box_divider_thin())
    lines.append(box_line(f"  Base Damage: {weapon.base_damage}"))
    lines.append(box_line(f"  Tags: [{tag_str}]"))

    if weapon.prefix:
        lines.append(box_divider())
        lines.append(box_line(f"  ▓ PREFIX: {weapon.prefix.name}"))
        lines.append(box_line(f"    {weapon.prefix.description}"))
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
        lines.append(box_line(f"  ▓ SUFFIX: {weapon.suffix.name}"))
        lines.append(box_line(f"    {weapon.suffix.description}"))
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
        lines.append(box_line(f"  ▓ SET BONUS: {weapon.set_bonus.name}"))
        lines.append(box_line(f"    {weapon.set_bonus.description}"))
    if weapon.flavor:
        lines.append(box_divider_pixel())
        lines.append(box_line(f'"{weapon.flavor}"', "center"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_between_floors(floor: int, interest: InterestManager, upgrade_shards: int = 0, flasks: int = 0) -> str:
    lines = [
        box_top(),
        box_blank(),
        box_line(f"░▒▓█  FLOOR {floor} COMPLETE  █▓▒░", "center"),
        box_blank(),
        box_divider(),
        box_line(f"  Patience: {patience_bar(interest)}"),
        box_line(f"  ◇ Upgrade Shards: {upgrade_shards}"),
        box_line(f"  ✚ Healing Flasks: {flasks}"),
        box_divider(),
    ]
    # Sera idle sprite
    for sl in sprites.SERA_IDLE.strip().split("\n"):
        lines.append(box_line(sl, "center"))
    lines.append(box_divider_thin())
    lines.append(box_line("  ▸ [1] Continue to next floor"))
    lines.append(box_line("  ▸ [2] Equip weapon"))
    lines.append(box_line("  ▸ [3] Craft (apply material to weapon)"))
    lines.append(box_line("  ▸ [4] Upgrade weapon (spend shards)"))
    lines.append(box_line("  ▸ [5] View inventory"))
    lines.append(box_line("  ▸ [6] Equipment menu"))
    lines.append(box_line("  ▸ [7] Quit"))
    lines.append(box_blank())
    lines.append(box_bot())
    return "\n".join(lines)


def render_equipment_menu(
    loadout: EquipmentLoadout,
    stash: list[EquipmentItem],
    stats: PlayerStats,
) -> str:
    lines = [
        box_top(),
        box_line("░▒▓█ EQUIPMENT MENU █▓▒░", "center"),
        box_divider(),
    ]

    for slot in SLOT_ORDER:
        item = loadout.equipped.get(slot)
        if item:
            lines.append(box_line(f"  [{slot}] {item.name} {item.ascii_art}"))
            lines.append(box_line(f"      +Stats: {item.stat_bonuses} | DR {item.damage_reduction} | RES {item.damage_resistance}%"))
            if item.resistances:
                lines.append(box_line(f"      Elem: {item.resistances}"))
            lines.append(box_line(f"      Ability: {item.ability or 'None'}"))
        else:
            lines.append(box_line(f"  [{slot}] (empty)"))
        lines.append(box_divider_thin())

    lines.append(box_header("TOTAL STATS"))
    lines.append(box_line("  " + " | ".join(stats.as_lines())))
    lines.append(box_blank())
    lines.append(box_header("STASH"))
    if stash:
        for i, item in enumerate(stash):
            lines.append(box_line(f"  ▸ [{i+1}] {item.name} ({item.slot}) {item.ascii_art}"))
    else:
        lines.append(box_line("  (no equipment items)"))
    lines.append(box_blank())
    lines.append(box_line("  ▸ [0] Back"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_game_over(interest: InterestManager, floor: int = 0) -> str:
    lines = [
        box_top(),
        box_blank(),
    ]
    # Game over art
    for art_line in sprites.GAME_OVER_ART.strip().split("\n"):
        lines.append(box_line(art_line, "center"))
    lines.append(box_blank())
    lines.append(box_line("G A M E   O V E R", "center"))
    lines.append(box_blank())
    lines.append(box_divider_pixel())
    lines.append(box_blank())
    lines.append(box_line('Sera rolls her eyes.', "center"))
    lines.append(box_line('"This is a waste of time."', "center"))
    lines.append(box_line('She teleports away.', "center"))
    lines.append(box_line('The dungeon collapses behind her.', "center"))
    lines.append(box_blank())
    lines.append(box_divider())
    lines.append(box_blank())
    lines.append(box_line(f"  ▓ Died on floor: {floor}"))
    lines.append(box_line(f"  ▓ Total kills:   {interest.total_kills}"))
    lines.append(box_line(f"  ▓ Turns survived:{interest.turn_number}"))
    lines.append(box_blank())
    lines.append(box_divider_pixel())
    lines.append(box_bot())
    return "\n".join(lines)


def render_victory(floor: int, interest: InterestManager) -> str:
    lines = [
        box_top(),
        box_blank(),
    ]
    # Victory art
    for art_line in sprites.VICTORY_ART.strip().split("\n"):
        lines.append(box_line(art_line, "center"))
    for art_line in sprites.CROWN.strip().split("\n"):
        lines.append(box_line(art_line, "center"))
    lines.append(box_blank())
    lines.append(box_line("D U N G E O N   C L E A R E D", "center"))
    lines.append(box_blank())
    lines.append(box_divider_pixel())
    lines.append(box_blank())
    lines.append(box_line('"...Acceptable."', "center"))
    lines.append(box_line('Sera nods once. The highest compliment.', "center"))
    lines.append(box_blank())
    lines.append(box_divider())
    lines.append(box_blank())
    lines.append(box_line(f"  ▓ Floors cleared:     {floor}"))
    lines.append(box_line(f"  ▓ Total kills:        {interest.total_kills}"))
    lines.append(box_line(f"  ▓ Patience remaining: {interest.current_patience}"))
    lines.append(box_blank())
    # Sera portrait for victory
    for sl in sprites.SERA_IDLE.strip().split("\n"):
        lines.append(box_line(sl, "center"))
    lines.append(box_blank())
    lines.append(box_divider_pixel())
    lines.append(box_bot())
    return "\n".join(lines)


def render_inspect(enemy: Enemy) -> str:
    lines = [
        box_top(),
        box_line(f"░▒▓ INSPECT: {enemy.name} ▓▒░", "center"),
        box_divider(),
    ]
    # Full enemy sprite
    sprite = sprites.get_enemy_sprite(enemy.archetype)
    for sl in sprite.strip().split("\n"):
        lines.append(box_line(sl, "center"))
    lines.append(box_divider_thin())
    lines.append(box_line(f"  Archetype:     {enemy.archetype}"))
    lines.append(box_line(f"  HP:            {hp_bar(enemy.current_hp, enemy.max_hp, 15)}"))
    if enemy.armor > 0:
        lines.append(box_line(f"  Armor:         {'▓' * min(enemy.armor, 10)} ({enemy.armor})"))
    else:
        lines.append(box_line(f"  Armor:         0"))
    if enemy.regen_per_turn > 0:
        lines.append(box_line(f"  Regen/turn:    +{enemy.regen_per_turn}"))
    req = enemy.vulnerability.name if enemy.vulnerability.name != "NONE" else "NONE (any weapon works)"
    lines.append(box_line(f"  Requires tag:  [{req}]"))
    if enemy.statuses:
        st = ", ".join(f"{s.effect.name}(p:{s.potency} t:{s.duration})" for s in enemy.statuses)
        lines.append(box_line(f"  Debuffs:       {st}"))
    if enemy.is_casting:
        lines.append(box_line(f"  ░░ CASTING: {enemy.pending_ability.name} ({enemy.cast_turns_remaining}t) ░░"))
    lines.append(box_divider())
    lines.append(box_header("ABILITIES"))
    for ab in enemy.abilities:
        cost = ANNOYANCE_COST[ab.annoyance]
        lines.append(box_line(f"  ▸ {ab.name} (-{cost} PP, {ab.annoyance.name})"))
        if ab.flavor:
            lines.append(box_line(f'    "{ab.flavor}"'))
    if enemy.flavor:
        lines.append(box_divider_pixel())
        lines.append(box_line(f'"{enemy.flavor}"', "center"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_dot_tick(dot_log: list[str], kill_name: str | None = None) -> str:
    lines = [
        box_top(),
    ]
    for art_line in sprites.DOT_TICK.strip().split("\n"):
        lines.append(box_line(art_line, "center"))
    lines.append(box_line("STATUS EFFECTS TICK", "center"))
    lines.append(box_divider())
    for entry in dot_log:
        lines.append(box_line(entry.strip()))
    if kill_name:
        lines.append(box_divider_pixel())
        lines.append(box_line(f"▓▓ {kill_name} dies to DOT! ▓▓", "center"))
        lines.append(box_line('"Slow death. How dramatic."', "center"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_dodge(enemy_name: str) -> str:
    lines = [
        box_top(),
    ]
    for art_line in sprites.DODGE_EFFECT.strip().split("\n"):
        lines.append(box_line(art_line, "center"))
    lines.append(box_line("░░ MISS! ░░", "center"))
    lines.append(box_divider())
    lines.append(box_line(f"  {enemy_name} dodges the attack!"))
    lines.append(box_line(f'  Sera: "Stand still, insect."'))
    lines.append(box_line(f"  [-2 Patience]"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_interrupt(enemy_name: str, ability_name: str) -> str:
    lines = [
        box_top(),
    ]
    for art_line in sprites.INTERRUPT_EFFECT.strip().split("\n"):
        lines.append(box_line(art_line, "center"))
    lines.append(box_line("▓▓ INTERRUPTED! ▓▓", "center"))
    lines.append(box_divider())
    lines.append(box_line(f"  {enemy_name}'s {ability_name} was cancelled!"))
    lines.append(box_line(f'  Sera: "I said shut up."'))
    lines.append(box_line(f"  [+3 Patience]"))
    lines.append(box_bot())
    return "\n".join(lines)


def get_input(prompt: str = "> ") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return "quit"
