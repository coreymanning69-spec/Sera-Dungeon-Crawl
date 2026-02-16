"""
Text-block UI renderer for SERA: ENDLESS ENGAGEMENT.

All display is box-drawn with simple ASCII blocks.
Numbers for input. Monospace assumed.
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
    bar = hp_bar(interest.current_patience, interest.max_patience, width=20)
    p = interest.current_patience
    if p <= 15:
        return bar + " !! CRITICAL !!"
    if p <= 30:
        return bar + " ! LOW !"
    return bar


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
        box_line("[2] Simulation Mode"),
        box_line("[3] Quit"),
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
        casting = " ** CASTING **" if e.is_casting else ""
        req = e.vulnerability.name.replace("REQUIRES_", "") if e.vulnerability.name != "NONE" else ""
        tag_hint = f" (needs [{req}])" if req else ""
        lines.append(box_line(f"  [{i+1}] {e.name}{casting}{tag_hint}"))
        lines.append(box_line(f"      HP: {hp_bar(e.current_hp, e.max_hp, 15)}"))
        if e.armor > 0:
            lines.append(box_line(f"      Armor: {e.armor}"))
        if e.statuses:
            st = ", ".join(f"{s.effect.name}({s.potency})" for s in e.statuses)
            lines.append(box_line(f"      [{st}]"))

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


def render_game_over(interest: InterestManager, floor: int = 0) -> str:
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
        box_line(f"Died on floor: {floor}"),
        box_line(f"Total kills: {interest.total_kills}"),
        box_line(f"Turns survived: {interest.turn_number}"),
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


def render_dot_tick(dot_log: list[str], kill_name: str | None = None) -> str:
    lines = [
        box_top(),
        box_line("STATUS EFFECTS TICK", "center"),
        box_divider(),
    ]
    for entry in dot_log:
        lines.append(box_line(entry.strip()))
    if kill_name:
        lines.append(box_divider())
        lines.append(box_line(f"{kill_name} dies to DOT!", "center"))
        lines.append(box_line('"Slow death. How dramatic."', "center"))
    lines.append(box_bot())
    return "\n".join(lines)


def render_dodge(enemy_name: str) -> str:
    lines = [
        box_top(),
        box_line("MISS!", "center"),
        box_divider(),
        box_line(f"  {enemy_name} dodges the attack!"),
        box_line(f'  Sera: "Stand still, insect."'),
        box_line(f"  [-2 Patience]"),
        box_bot(),
    ]
    return "\n".join(lines)


def render_interrupt(enemy_name: str, ability_name: str) -> str:
    lines = [
        box_top(),
        box_line("INTERRUPTED!", "center"),
        box_divider(),
        box_line(f"  {enemy_name}'s {ability_name} was cancelled!"),
        box_line(f'  Sera: "I said shut up."'),
        box_line(f"  [+3 Patience]"),
        box_bot(),
    ]
    return "\n".join(lines)


def render_sim_summary(results: list[dict]) -> str:
    """Render a compact summary table for simulation scenarios."""
    lines = [
        box_top(),
        box_blank(),
        box_line("S I M U L A T I O N   R E S U L T S", "center"),
        box_blank(),
        box_divider(),
    ]
    for i, r in enumerate(results):
        status = "GAME OVER" if r["game_over"] else "SURVIVED"
        lines.append(box_line(f"  [{i+1}] {r['name']}"))
        lines.append(box_line(
            f"      {status}  |  Kills: {r['kills']}  "
            f"|  Patience: {r['patience']}/{r['max_patience']}  "
            f"|  Turns: {r['turns']}"
        ))
        lines.append(box_blank())
    lines.append(box_divider())
    lines.append(box_line("[#] View scenario details   [0] Back"))
    lines.append(box_blank())
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
        box_line("[5] View run stats"),
        box_line("[6] Quit"),
        box_blank(),
        box_bot(),
    ]
    return "\n".join(lines)


def get_input(prompt: str = "> ") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return "quit"
