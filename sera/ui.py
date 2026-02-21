"""
Pixel Art UI renderer for SERA: ENDLESS ENGAGEMENT.

Old-school 64/128-bit retro aesthetic using Unicode block
characters (░▒▓█▀▄▐▌) and box-drawing (╔╗╚╝║═).
Monospace terminal assumed.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from sera.weapon import Weapon
from sera.enemy import Enemy, ANNOYANCE_COST
from sera.interest import InterestManager
from sera.crafting import CraftingMaterial
from sera.equipment import EquipmentItem, EquipmentLoadout, SLOT_ORDER
from sera.stats import PlayerStats
from sera import sprites


# ─────────────────────────────────────────────────────────
# Pixel UI system (overlay architecture)
# ─────────────────────────────────────────────────────────


class UIStateType(str, Enum):
    VIEWPORT = "VIEWPORT"
    OVERLAY = "OVERLAY"
    MODAL = "MODAL"


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h


@dataclass(frozen=True)
class UIEvent:
    event_type: str
    x: int = 0
    y: int = 0
    key: str = ""


@dataclass(frozen=True)
class UIRequest:
    request_type: str
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class EventResult:
    consumed: bool
    request: UIRequest | None = None


class IWidget:
    id: str
    rect: Rect
    visible: bool
    enabled: bool

    def layout(self, _ctx: dict[str, object] | None = None):
        return None

    def render(self, _ctx: dict[str, object] | None = None) -> list[tuple[int, str]]:
        return []

    def handle_event(self, _ev: UIEvent) -> EventResult:
        return EventResult(consumed=False)

    def hit_test(self, x: int, y: int) -> bool:
        return self.rect.contains(x, y)


class IOverlay(IWidget):
    overlay_id: str

    def open(self, payload: dict[str, object] | None = None):
        _ = payload
        self.visible = True

    def close(self):
        self.visible = False

    def is_blocking_viewport(self) -> bool:
        return True


class PanelOverlay(IOverlay):
    def __init__(
        self,
        overlay_id: str,
        rect: Rect,
        title: str,
        *,
        blocking: bool,
        action_buttons: list[Rect] | None = None,
    ):
        self.id = overlay_id
        self.overlay_id = overlay_id
        self.rect = rect
        self.title = title
        self.visible = False
        self.enabled = True
        self.blocking = blocking
        self.action_buttons = action_buttons or []

    def render(self, _ctx: dict[str, object] | None = None) -> list[tuple[int, str]]:
        if not self.visible:
            return []
        layer = 700 if self.blocking else 300
        return [(200, f"panel:{self.overlay_id}:{self.rect}"), (layer, f"title:{self.title}")]

    def is_blocking_viewport(self) -> bool:
        return self.blocking

    def handle_event(self, ev: UIEvent) -> EventResult:
        if not self.visible or not self.enabled:
            return EventResult(consumed=False)

        if self.blocking:
            if ev.event_type == "key" and ev.key.lower() == "esc":
                return EventResult(consumed=True, request=UIRequest("CloseOverlay"))
            return EventResult(consumed=True)

        if ev.event_type == "click":
            for button in self.action_buttons:
                if button.contains(ev.x, ev.y):
                    return EventResult(consumed=True)
        return EventResult(consumed=False)


class BottomBar(IWidget):
    def __init__(self, rect: Rect):
        self.id = "bottom_bar"
        self.rect = rect
        self.visible = True
        self.enabled = True
        self._icon_hitboxes: dict[str, Rect] = {}

    def set_icon_hitboxes(self, icon_hitboxes: dict[str, Rect]):
        self._icon_hitboxes = icon_hitboxes

    def render(self, _ctx: dict[str, object] | None = None) -> list[tuple[int, str]]:
        return [(100, "bottom_bar")]

    def handle_event(self, ev: UIEvent) -> EventResult:
        if not self.visible or not self.enabled or ev.event_type != "click":
            return EventResult(consumed=False)
        for overlay_id, rect in self._icon_hitboxes.items():
            if rect.contains(ev.x, ev.y):
                return EventResult(
                    consumed=True,
                    request=UIRequest("OpenOverlay", {"overlay_id": overlay_id}),
                )
        return EventResult(consumed=False)


@dataclass
class UIState:
    state_type: UIStateType = UIStateType.VIEWPORT
    open_overlay_id: str | None = None
    modal_id: str | None = None
    previous_state: "UIState | None" = None


class UIRoot:
    def __init__(self, bottom_bar: BottomBar, viewport_handler: Callable[[UIEvent], EventResult] | None = None):
        self.state = UIState()
        self.overlays: dict[str, IOverlay] = {}
        self.bottom_bar = bottom_bar
        self.viewport_handler = viewport_handler or (lambda _ev: EventResult(consumed=False))
        self.context_menu_handler: Callable[[UIEvent], EventResult] | None = None
        self.modal_handler: Callable[[UIEvent], EventResult] | None = None

    def register_overlay(self, overlay: IOverlay):
        self.overlays[overlay.overlay_id] = overlay

    def _active_overlay(self) -> IOverlay | None:
        if self.state.open_overlay_id is None:
            return None
        return self.overlays.get(self.state.open_overlay_id)

    def open_overlay(self, overlay_id: str, payload: dict[str, object] | None = None):
        if self.state.state_type == UIStateType.MODAL:
            return
        current = self._active_overlay()
        if current and current.overlay_id == overlay_id:
            self.close_overlay()
            return
        if current:
            current.close()
        target = self.overlays[overlay_id]
        target.open(payload)
        self.state = UIState(state_type=UIStateType.OVERLAY, open_overlay_id=overlay_id)

    def close_overlay(self):
        current = self._active_overlay()
        if current:
            current.close()
        self.state = UIState(state_type=UIStateType.VIEWPORT)

    def open_modal(self, modal_id: str):
        self.state = UIState(
            state_type=UIStateType.MODAL,
            modal_id=modal_id,
            previous_state=self.state,
        )

    def close_modal(self):
        if self.state.state_type != UIStateType.MODAL:
            return
        self.state = self.state.previous_state or UIState()

    def is_viewport_suspended(self) -> bool:
        if self.state.state_type == UIStateType.MODAL:
            return True
        overlay = self._active_overlay()
        return bool(overlay and overlay.is_blocking_viewport())

    def _apply_request(self, req: UIRequest):
        if req.request_type == "OpenOverlay":
            overlay_id = str(req.payload.get("overlay_id", ""))
            if overlay_id:
                self.open_overlay(overlay_id, req.payload)
        elif req.request_type == "CloseOverlay":
            self.close_overlay()
        elif req.request_type == "OpenModal":
            modal_id = str(req.payload.get("modal_id", "modal"))
            self.open_modal(modal_id)
        elif req.request_type == "CloseModal":
            self.close_modal()

    def _run_handler(self, handler: Callable[[UIEvent], EventResult] | None, ev: UIEvent) -> bool:
        if handler is None:
            return False
        result = handler(ev)
        if result.request:
            self._apply_request(result.request)
        return result.consumed

    def dispatch_event(self, ev: UIEvent) -> EventResult:
        if ev.event_type == "key" and ev.key.lower() == "esc":
            if self.state.state_type == UIStateType.MODAL:
                self.close_modal()
                return EventResult(consumed=True)
            if self.state.state_type == UIStateType.OVERLAY:
                self.close_overlay()
                return EventResult(consumed=True)
            self.open_overlay("system_menu")
            return EventResult(consumed=True)

        if self.state.state_type == UIStateType.MODAL and self._run_handler(self.modal_handler, ev):
            return EventResult(consumed=True)
        if self._run_handler(self.context_menu_handler, ev):
            return EventResult(consumed=True)

        overlay = self._active_overlay()
        if overlay:
            result = overlay.handle_event(ev)
            if result.request:
                self._apply_request(result.request)
            if result.consumed:
                return EventResult(consumed=True)

        bar_result = self.bottom_bar.handle_event(ev)
        if bar_result.request:
            self._apply_request(bar_result.request)
        if bar_result.consumed:
            return EventResult(consumed=True)

        viewport_result = self.viewport_handler(ev)
        if viewport_result.request:
            self._apply_request(viewport_result.request)
        return viewport_result

    def render(self, ctx: dict[str, object] | None = None) -> list[tuple[int, str]]:
        draw_ops = [(0, "viewport")]
        draw_ops.extend(self.bottom_bar.render(ctx))
        overlay = self._active_overlay()
        if overlay:
            draw_ops.extend(overlay.render(ctx))
        draw_ops.sort(key=lambda item: item[0])
        return draw_ops


def build_default_ui_root(viewport_handler: Callable[[UIEvent], EventResult] | None = None) -> UIRoot:
    bottom_bar = BottomBar(Rect(0, 180, 320, 20))
    bottom_bar.set_icon_hitboxes(
        {
            "system_menu": Rect(4, 182, 16, 16),
            "status_screen": Rect(24, 182, 16, 16),
            "loadout_screen": Rect(44, 182, 16, 16),
            "log_screen": Rect(64, 182, 16, 16),
        }
    )
    root = UIRoot(bottom_bar=bottom_bar, viewport_handler=viewport_handler)
    root.register_overlay(PanelOverlay("system_menu", Rect(60, 20, 200, 150), "System", blocking=True))
    root.register_overlay(
        PanelOverlay(
            "status_screen",
            Rect(8, 8, 144, 112),
            "Status",
            blocking=False,
            action_buttons=[Rect(16, 30, 60, 16), Rect(16, 50, 60, 16)],
        )
    )
    root.register_overlay(
        PanelOverlay(
            "loadout_screen",
            Rect(160, 8, 152, 112),
            "Loadout",
            blocking=False,
            action_buttons=[Rect(168, 32, 120, 16)],
        )
    )
    root.register_overlay(
        PanelOverlay(
            "log_screen",
            Rect(8, 122, 304, 56),
            "Log",
            blocking=False,
            action_buttons=[Rect(16, 130, 288, 40)],
        )
    )
    return root


# ─────────────────────────────────────────────────────────
# Pixel-style interface art (filesystem-friendly mockups)
# ─────────────────────────────────────────────────────────

_UI_FRAME_WIDTH = 76
_UI_VIEWPORT_HEIGHT = 16


def _frame_border(width: int = _UI_FRAME_WIDTH) -> str:
    return "+" + "-" * (width - 2) + "+"


def _frame_line(text: str = "", width: int = _UI_FRAME_WIDTH) -> str:
    inner = width - 4
    return f"| {text[:inner].ljust(inner)} |"


def _overlay_art_lines(overlay_id: str) -> list[str]:
    if overlay_id == "system_menu":
        return [
            "[ SYSTEM ]",
            "  > Save Run",
            "  > Options",
            "  > Return to Title",
            "  > Exit",
            "",
            "(Blocking: combat suspended)",
        ]
    if overlay_id == "status_screen":
        return [
            "[ STATUS ]",
            "HP: ########## 999/999",
            "Dmg Type: PHYSICAL | BLEED",
            "Resist: FIRE 20% | ARCANE 40%",
            "Statuses: Marked(2), Haste(1)",
            "Run: Floor 3 | Kills 27 | Turns 44",
            "",
            "(Non-blocking: pass-through outside widgets)",
        ]
    if overlay_id == "loadout_screen":
        return [
            "[ LOADOUT ]",
            "Weapon: Petty Rusty Shiv of Agony",
            "Armor : Threaded Moonplate",
            "Charm : Sunshard Loop",
            "",
            "[1] Equip  [2] Swap Set",
            "",
            "(Non-blocking: pass-through outside widgets)",
        ]
    if overlay_id == "log_screen":
        return [
            "[ LOG ]",
            "> You hit Clanking Dreadknight for 12",
            "> BLEED ticks for 3",
            "> Dreadknight begins Oath of Honor",
            "> Interrupted! +3 Patience",
            "",
            "[Chat] Sera: \"Adequate violence.\"",
            "(Non-blocking: pass-through outside widgets)",
        ]
    return []


def render_pixel_interface_art(root: UIRoot, combat_lines: list[str] | None = None) -> str:
    """Render an ASCII pixel-style interface frame for filesystem previews."""
    combat_lines = combat_lines or [
        "Viewport: combat updates continuously unless blocked.",
        "Enemy: Clanking Dreadknight  HP [#####-----] 26/50",
        "Sera: \"Entertain me.\"",
    ]

    lines = [_frame_border()]
    lines.append(_frame_line("SERA PIXEL UI PREVIEW"))
    lines.append(_frame_line("=" * (_UI_FRAME_WIDTH - 4)))

    for idx in range(_UI_VIEWPORT_HEIGHT):
        row = combat_lines[idx] if idx < len(combat_lines) else ""
        lines.append(_frame_line(row))

    lines.append(_frame_line("-" * (_UI_FRAME_WIDTH - 4)))

    active_id = root.state.open_overlay_id or "none"
    lines.append(
        _frame_line(
            f"BottomBar: [SYS] [STATUS] [LOADOUT] [LOG]      active={active_id}"
        )
    )

    overlay = root._active_overlay()
    if overlay:
        lines.append(_frame_line("=" * (_UI_FRAME_WIDTH - 4)))
        for row in _overlay_art_lines(overlay.overlay_id):
            lines.append(_frame_line(row))

    lines.append(_frame_border())
    return "\n".join(lines)


def export_pixel_ui_mockups(output_dir: str = "docs/pixel-ui") -> list[str]:
    """Write pixel-style interface mockups to filesystem for quick review."""
    from pathlib import Path

    root = build_default_ui_root()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    written: list[str] = []

    viewport = out / "viewport.txt"
    viewport.write_text(render_pixel_interface_art(root) + "\n")
    written.append(str(viewport))

    for overlay_id in ["system_menu", "status_screen", "loadout_screen", "log_screen"]:
        root.open_overlay(overlay_id)
        target = out / f"{overlay_id}.txt"
        target.write_text(render_pixel_interface_art(root) + "\n")
        written.append(str(target))

    return written


# ─────────────────────────────────────────────────────────
# Drawing primitives — retro pixel style
# ─────────────────────────────────────────────────────────

W = 126  # less wide viewport for cleaner terminal readability


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

TITLE_ART = [
    "   _____  _____  ____   ___   ",
    "  / ___/ / ___/ / __ \\ /   |  ",
    "  \\__ \\  \\__ \\ / /_/ // /| |  ",
    " ___/ / ___/ // _, _// ___ |  ",
    "/____/ /____//_/ |_|/_/  |_|  ",
]

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
    lines.append(box_blank())
    import random
    title_quotes = [
        '"I am a Goddess. Entertain me."',
        '"Nothing in this cosmos is interesting. Prove me wrong."',
        '"I don\'t think there\'s anything at all that can stop me."',
        '"Fine. Let\'s see what you\'ve got."',
    ]
    lines.append(box_line(random.choice(title_quotes), "center"))
    lines.append(box_divider())
    lines.append(box_blank())
    lines.append(box_line("  ▸ [1] New Game"))
    lines.append(box_line("  ▸ [2] Simulation Mode"))
    lines.append(box_line("  ▸ [3] Quit"))
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
        sprite_lines = sprites.get_enemy_sprite(e.archetype, e.name).strip().split("\n")
        # Just show first 3 lines of sprite as a preview
        for sl in sprite_lines[:3]:
            lines.append(box_line(f"  {sl}"))
        lines.append(box_line(f"  [{i+1}] {e.name} ({e.archetype})"))
        lines.append(box_line(f"      HP: {hp_bar(e.current_hp, e.max_hp, 15)}"))
        if e.armor > 0:
            lines.append(box_line(f"      Armor: {'▓' * e.armor}  ({e.armor})"))
        lines.append(box_line(f"      Requires: [{tag_req}]"))
        if e.elemental_weaknesses:
            weak = ", ".join(tag.name for tag in e.elemental_weaknesses)
            lines.append(box_line(f"      Weak: {weak}"))
        if e.elemental_resistances:
            resist = ", ".join(tag.name for tag in e.elemental_resistances)
            lines.append(box_line(f"      Resist: {resist}"))
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
        if e.elemental_weaknesses or e.elemental_resistances:
            elem_parts = []
            if e.elemental_weaknesses:
                elem_parts.append("Weak:" + ",".join(t.name for t in e.elemental_weaknesses))
            if e.elemental_resistances:
                elem_parts.append("Resist:" + ",".join(t.name for t in e.elemental_resistances))
            lines.append(box_line(f"        [{' | '.join(elem_parts)}]"))
        if e.statuses:
            st = ", ".join(f"{s.effect.name}({s.potency})" for s in e.statuses)
            lines.append(box_line(f"        [{st}]"))

    lines.append(box_divider())
    lines.append(box_header("ACTIONS"))
    for i, e in enumerate(alive):
        lines.append(box_line(f"  ▸ [{i+1}] Attack {e.name}"))
    lines.append(box_line(f"  ▸ [I] Inspect enemy"))
    lines.append(box_blank())
    lines.append(box_line(f"  ▸ [W] View weapon details"))
    lines.append(box_blank())
    lines.append(box_line(f"  ▸ [H] Use healing flask"))
    lines.append(box_blank())
    lines.append(box_line(f"  ▸ [A] Auto-battle ({10} turns)"))
    lines.append(box_blank())
    lines.append(box_line(f"  ▸ [0] Commands menu (cheat/debug)"))
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
    sprite_lines = sprites.get_enemy_sprite(enemy.archetype, enemy.name).strip().split("\n")
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
    lines.append(box_blank())
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
        lines.append(box_blank())
        choices.append(("weapon", idx))
        idx += 1

    if material_loot:
        tag_name = material_loot.grants_tag.name if material_loot.grants_tag else "???"
        lines.append(box_line(f"  ▸ [{idx}] {material_loot.name} (grants [{tag_name}])"))
        if material_loot.flavor:
            lines.append(box_line(f'        {material_loot.flavor}'))
        lines.append(box_blank())
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


def render_between_floors(
    floor: int,
    interest: InterestManager,
    upgrade_shards: int = 0,
    flasks: int = 0,
    revision_set: list[EquipmentItem] | None = None,
    revision_claimed: bool = False,
) -> str:
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
    if revision_set:
        lines.append(box_divider_thin())
        status = "CLAIMED" if revision_claimed else "READY"
        lines.append(box_line(f"  Next Revision Kit: {len(revision_set)} pieces [{status}]"))
        preview = ", ".join(item.slot for item in revision_set[:4])
        if preview:
            lines.append(box_line(f"    Preview slots: {preview}"))
    lines.append(box_line("  ▸ [1] Continue to next floor"))
    lines.append(box_line("  ▸ [2] Equip weapon"))
    lines.append(box_line("  ▸ [3] Craft (apply material to weapon)"))
    lines.append(box_line("  ▸ [4] Upgrade weapon (spend shards)"))
    lines.append(box_line("  ▸ [5] View inventory"))
    lines.append(box_line("  ▸ [6] Equipment menu"))
    lines.append(box_line("  ▸ [7] Claim next-revision gear set"))
    lines.append(box_line("  ▸ [8] View Run Stats"))
    lines.append(box_line("  ▸ [9] Quit"))
    lines.append(box_blank())
    lines.append(box_bot())
    return "\n".join(lines)




def render_auto_battle_screen(turn_results: list[dict], total_damage: int, total_kills: int, patience: int, max_patience: int) -> str:
    """Render live auto-battle telemetry for quick turn-by-turn updates."""
    lines = [
        box_top(),
        box_line("░▒▓█ AUTO BATTLE FEED █▓▒░", "center"),
        box_divider(),
        box_line(f"  Total Damage: {total_damage}"),
        box_line(f"  Total Kills: {total_kills}"),
        box_line(f"  Patience: {patience}/{max_patience}"),
        box_divider(),
    ]
    for result in turn_results[-6:]:
        lines.append(box_line(f"  Turn {result['turn']}: {result['target']} for {result['damage']} ({result['target_hp']})"))
        if result["kills"] > 0:
            lines.append(box_line(f"      Kills +{result['kills']} | Patience now {result['patience']}"))
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
    sprite = sprites.get_enemy_sprite(enemy.archetype, enemy.name)
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
    if enemy.elemental_weaknesses:
        weak = ", ".join(tag.name for tag in enemy.elemental_weaknesses)
        lines.append(box_line(f"  Weak to:       [{weak}] (+2 dmg each)"))
    if enemy.elemental_resistances:
        resist = ", ".join(tag.name for tag in enemy.elemental_resistances)
        lines.append(box_line(f"  Resists:       [{resist}] (-1 dmg each)"))
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


def render_sim_summary(results: list[dict]) -> str:
    """Render a simulation summary table for all scenarios."""
    lines = [
        box_top(),
        box_blank(),
        box_line("░▒▓█ SIMULATION SUMMARY █▓▒░", "center"),
        box_blank(),
        box_divider(),
        box_line(f"  {'#':<4} {'Scenario':<24} {'Kills':<7} {'Pat':<8} {'Turns':<6}"),
        box_divider_thin(),
    ]
    for i, r in enumerate(results, 1):
        name = r.get("name", f"Scenario {i}")[:24]
        kills = r.get("kills", "?")
        pat = f"{r.get('patience', '?')}/{r.get('max_patience', '?')}"
        turns = r.get("turns", "?")
        over = " GAME OVER" if r.get("game_over") else ""
        lines.append(box_line(f"  {i:<4} {name:<24} {kills:<7} {pat:<8} {turns:<6}{over}"))
    lines.append(box_blank())
    lines.append(box_divider_pixel())
    lines.append(box_line('Sera: "Not bad. Not GOOD, but not bad."', "center"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_sim_detail(result: dict) -> str:
    """Render the full log for a single simulation scenario."""
    lines = [
        box_top(),
        box_line(f"SCENARIO: {result['name']}", "center"),
        box_divider(),
    ]
    for log_line in result["log"]:
        stripped = log_line.rstrip()
        if len(stripped) > W - 4:
            stripped = stripped[:W - 7] + "..."
        lines.append(box_line(stripped))
    lines.append(box_divider())
    lines.append(box_line("[Enter] Back to summary"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_run_stats(stats: dict) -> str:
    """Render end-of-run or mid-run statistics."""
    lines = [
        box_top(),
        box_line("R U N   S T A T S", "center"),
        box_divider(),
        box_line(f"  Floors cleared:     {stats.get('floors_cleared', 0)}"),
        box_line(f"  Total kills:        {stats.get('total_kills', 0)}"),
        box_line(f"  Total turns:        {stats.get('total_turns', 0)}"),
        box_line(f"  Total damage dealt: {stats.get('total_damage', 0)}"),
        box_line(f"  Best overkill:      {stats.get('best_overkill', 0)}"),
        box_line(f"  Weapons found:      {stats.get('weapons_found', 0)}"),
        box_line(f"  Materials used:     {stats.get('materials_used', 0)}"),
        box_divider(),
        box_line(f"  Patience remaining: {stats.get('patience', 0)}/{stats.get('max_patience', 100)}"),
    ]
    if stats.get("weapon_name"):
        lines.append(box_line(f"  Final weapon:       {stats['weapon_name']}"))
    lines.append(box_blank())
    lines.append(box_bot())
    return "\n".join(lines)


def render_post_game(stats: dict, won: bool) -> str:
    """Render the post-game screen with play again option."""
    if won:
        header = "D U N G E O N  C L E A R E D"
        sera_line = '"...Acceptable."'
    else:
        header = "G A M E   O V E R"
        sera_line = '"This is a waste of time."'

    lines = [
        box_top(),
        box_blank(),
        box_line(header, "center"),
        box_blank(),
        box_divider(),
        box_line(sera_line, "center"),
        box_divider(),
        box_blank(),
        box_line(f"  Floors cleared:     {stats.get('floors_cleared', 0)}"),
        box_line(f"  Total kills:        {stats.get('total_kills', 0)}"),
        box_line(f"  Total turns:        {stats.get('total_turns', 0)}"),
        box_line(f"  Total damage dealt: {stats.get('total_damage', 0)}"),
        box_line(f"  Best overkill:      {stats.get('best_overkill', 0)}"),
        box_blank(),
        box_divider(),
        box_line("[1] Play Again"),
        box_line("[2] Return to Menu"),
        box_blank(),
        box_bot(),
    ]
    return "\n".join(lines)


def get_input(prompt: str = "> ") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return "quit"


# ─────────────────────────────────────────────────────────
# Pixel UI overlay system
# ─────────────────────────────────────────────────────────


@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px < (self.x + self.width) and self.y <= py < (self.y + self.height)


@dataclass
class UIEvent:
    event_type: str
    x: int = 0
    y: int = 0
    key: str = ""


@dataclass
class EventResult:
    consumed: bool = False


class UIStateType(Enum):
    VIEWPORT = "VIEWPORT"
    OVERLAY = "OVERLAY"
    MODAL = "MODAL"


@dataclass
class UIState:
    state_type: UIStateType = UIStateType.VIEWPORT
    open_overlay_id: str | None = None
    modal_id: str | None = None
    modal_previous_state: tuple[UIStateType, str | None] | None = None


@dataclass
class Overlay:
    overlay_id: str
    title: str
    blocking_viewport: bool
    interactive_hitboxes: list[Rect] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)

    def is_blocking_viewport(self) -> bool:
        return self.blocking_viewport

    def handle_event(self, event: UIEvent) -> EventResult:
        if self.blocking_viewport:
            return EventResult(consumed=True)
        if event.event_type != "click":
            return EventResult(consumed=False)
        consumed = any(rect.contains(event.x, event.y) for rect in self.interactive_hitboxes)
        return EventResult(consumed=consumed)


class UIRoot:
    def __init__(
        self,
        overlays: dict[str, Overlay],
        viewport_handler,
        bottom_bar_hitboxes: dict[str, Rect],
    ):
        self.overlays = overlays
        self.viewport_handler = viewport_handler
        self.bottom_bar_hitboxes = bottom_bar_hitboxes
        self.state = UIState()

    def open_overlay(self, overlay_id: str):
        if overlay_id not in self.overlays:
            return
        if self.state.state_type == UIStateType.MODAL:
            return
        if self.state.state_type == UIStateType.OVERLAY and self.state.open_overlay_id == overlay_id:
            self.state = UIState(state_type=UIStateType.VIEWPORT)
            return
        self.state = UIState(state_type=UIStateType.OVERLAY, open_overlay_id=overlay_id)

    def dismiss_active_overlay(self):
        if self.state.state_type == UIStateType.OVERLAY:
            self.state = UIState(state_type=UIStateType.VIEWPORT)

    def is_viewport_suspended(self) -> bool:
        if self.state.state_type == UIStateType.MODAL:
            return True
        if self.state.state_type == UIStateType.OVERLAY and self.state.open_overlay_id:
            overlay = self.overlays[self.state.open_overlay_id]
            return overlay.is_blocking_viewport()
        return False

    def _handle_esc(self):
        if self.state.state_type == UIStateType.MODAL and self.state.modal_previous_state:
            prev_type, prev_overlay = self.state.modal_previous_state
            self.state = UIState(state_type=prev_type, open_overlay_id=prev_overlay)
            return
        if self.state.state_type == UIStateType.OVERLAY:
            self.state = UIState(state_type=UIStateType.VIEWPORT)
            return
        self.open_overlay("system_menu")

    def _dispatch_bottom_bar(self, event: UIEvent) -> EventResult:
        if event.event_type != "click":
            return EventResult(consumed=False)
        for overlay_id, rect in self.bottom_bar_hitboxes.items():
            if rect.contains(event.x, event.y):
                self.open_overlay(overlay_id)
                return EventResult(consumed=True)
        return EventResult(consumed=False)

    def dispatch_event(self, event: UIEvent) -> EventResult:
        if event.event_type == "key" and event.key.lower() == "esc":
            self._handle_esc()
            return EventResult(consumed=True)

        if self.state.state_type == UIStateType.MODAL:
            return EventResult(consumed=True)

        if self.state.state_type == UIStateType.OVERLAY and self.state.open_overlay_id:
            overlay_result = self.overlays[self.state.open_overlay_id].handle_event(event)
            if overlay_result.consumed:
                return overlay_result

        bar_result = self._dispatch_bottom_bar(event)
        if bar_result.consumed:
            return bar_result

        return self.viewport_handler(event)


def _default_viewport_handler(_event: UIEvent) -> EventResult:
    return EventResult(consumed=True)


def build_default_ui_root(viewport_handler=None) -> UIRoot:
    status_overlay = Overlay(
        overlay_id="status_screen",
        title="STATUS",
        blocking_viewport=False,
        interactive_hitboxes=[Rect(8, 30, 56, 8)],
        lines=[
            "HP: ########## 999/999",
            "Dmg Type: PHYSICAL | BLEED",
            "Resist: FIRE 20% | ARCANE 40%",
            "Statuses: Marked(2), Haste(1)",
            "Run: Floor 3 | Kills 27 | Turns 44",
            "",
            "(Non-blocking: pass-through outside widgets)",
        ],
    )
    loadout_overlay = Overlay(
        overlay_id="loadout_screen",
        title="LOADOUT",
        blocking_viewport=False,
        interactive_hitboxes=[Rect(8, 30, 56, 8)],
        lines=[
            "Weapon: Petty Rusty Shiv of Agony",
            "Armor : Threaded Moonplate",
            "Charm : Sunshard Loop",
            "",
            "[1] Equip  [2] Swap Set",
            "",
            "(Non-blocking: pass-through outside widgets)",
        ],
    )
    log_overlay = Overlay(
        overlay_id="log_screen",
        title="LOG",
        blocking_viewport=False,
        interactive_hitboxes=[Rect(8, 30, 56, 8)],
        lines=[
            "> You hit Clanking Dreadknight for 12",
            "> BLEED ticks for 3",
            "> Dreadknight begins Oath of Honor",
            "> Interrupted! +3 Patience",
            "",
            "[Chat] Sera: \"Adequate violence.\"",
            "(Non-blocking: pass-through outside widgets)",
        ],
    )
    system_overlay = Overlay(
        overlay_id="system_menu",
        title="SYSTEM",
        blocking_viewport=True,
        lines=[
            "  > Save Run",
            "  > Options",
            "  > Return to Title",
            "  > Exit",
            "",
            "(Blocking: combat suspended)",
        ],
    )

    overlays = {
        o.overlay_id: o
        for o in [system_overlay, status_overlay, loadout_overlay, log_overlay]
    }
    bottom_bar_hitboxes = {
        "system_menu": Rect(10, 20, 6, 2),
        "status_screen": Rect(18, 20, 9, 2),
        "loadout_screen": Rect(29, 20, 10, 2),
        "log_screen": Rect(41, 20, 6, 2),
    }
    return UIRoot(
        overlays=overlays,
        viewport_handler=viewport_handler or _default_viewport_handler,
        bottom_bar_hitboxes=bottom_bar_hitboxes,
    )


def _frame_line(text: str) -> str:
    inner = 74
    return "| " + text.ljust(inner) + " |"


def render_pixel_interface_art(root: UIRoot) -> str:
    active_id = root.state.open_overlay_id or "none"
    lines = [
        "+--------------------------------------------------------------------------+",
        _frame_line("SERA PIXEL UI PREVIEW"),
        _frame_line("========================================================================"),
        _frame_line("Viewport: combat updates continuously unless blocked."),
        _frame_line("Enemy: Clanking Dreadknight  HP [#####-----] 26/50"),
        _frame_line('Sera: "Entertain me."'),
    ]
    for _ in range(12):
        lines.append(_frame_line(""))
    lines.append(_frame_line("------------------------------------------------------------------------"))
    lines.append(_frame_line(f"BottomBar: [SYS] [STATUS] [LOADOUT] [LOG]      active={active_id}"))

    if root.state.state_type == UIStateType.OVERLAY and root.state.open_overlay_id:
        overlay = root.overlays[root.state.open_overlay_id]
        lines.append(_frame_line("========================================================================"))
        lines.append(_frame_line(f"[ {overlay.title} ]"))
        for overlay_line in overlay.lines:
            lines.append(_frame_line(overlay_line))

    lines.append("+--------------------------------------------------------------------------+")
    return "\n".join(lines)


def export_pixel_ui_mockups(output_dir: str) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    root = build_default_ui_root()
    outputs = [("viewport.txt", render_pixel_interface_art(root))]
    for overlay_id in ["system_menu", "status_screen", "loadout_screen", "log_screen"]:
        root.open_overlay(overlay_id)
        outputs.append((f"{overlay_id if overlay_id != 'system_menu' else 'system_menu'}.txt", render_pixel_interface_art(root)))

    written: list[str] = []
    for filename, content in outputs:
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        written.append(path)
    return written
