# Pixel UI Overlay System

This project now includes a UI state machine that keeps combat viewport flow active by default and treats most menus as fast, non-blocking overlays.

## Core regions

- **Viewport**: combat simulation surface.
- **BottomBar**: persistent icon row that toggles overlays.
- **Overlays**:
  - `system_menu` (**blocking**)
  - `status_screen` (**non-blocking**)
  - `loadout_screen` (**non-blocking**)
  - `log_screen` (**non-blocking**)
- **Modal**: optional blocking layer for confirmations.

## State machine

- `VIEWPORT`
- `OVERLAY(open_overlay_id)`
- `MODAL(modal_id, previous_state)`

Transitions:

- BottomBar icon press:
  - `VIEWPORT -> OVERLAY(id)`
  - `OVERLAY(id) -> VIEWPORT` (toggle off)
  - `OVERLAY(other) -> OVERLAY(id)` (swap)
  - `MODAL(*) -> ignore`
- `Esc` / back:
  - `MODAL -> previous_state`
  - `OVERLAY(*) -> VIEWPORT`
  - `VIEWPORT -> OVERLAY(system_menu)`

## Blocking policy

`IOverlay.is_blocking_viewport()` controls simulation/input suspension.

- `system_menu` returns `True`.
- `status_screen`, `loadout_screen`, and `log_screen` return `False`.

`UIRoot.is_viewport_suspended()` is `True` for modal state or a blocking overlay.

## Input routing order

`UIRoot.dispatch_event` applies this priority:

1. Modal layer (if active)
2. Context menu layer (if active)
3. Active overlay
4. BottomBar
5. Viewport

### Non-blocking pass-through rule

Non-blocking overlays only consume clicks inside interactive widget hitboxes. Clicks elsewhere are not consumed and pass through to the viewport handler so combat can continue uninterrupted.

### Blocking rule

Blocking overlays consume all input. This keeps `system_menu` as the single pause/suspend UI.

## Rendering layers

The UI root emits layer-ordered draw operations:

- `0`: viewport
- `100`: bottom bar
- `200`: overlay base panels
- `300`: overlay widgets (or `700` for blocking system overlay)

## Pixel constraints in code

The UI primitives use integer-only geometry (`Rect` with `int` members) and integer hit testing.

## Sera constraint

The UI does not assume HP-based hard death fail states; run tension remains a pacing/interest model and overlay behavior is independent from hard-death flows.
