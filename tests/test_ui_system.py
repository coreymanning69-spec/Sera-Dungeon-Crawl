import unittest

from sera.ui import EventResult, UIEvent, build_default_ui_root, render_pixel_interface_art


class TestPixelUISystem(unittest.TestCase):
    def test_overlay_toggle_and_swap_behavior(self):
        root = build_default_ui_root()

        root.open_overlay("status_screen")
        self.assertEqual(root.state.open_overlay_id, "status_screen")

        root.open_overlay("status_screen")
        self.assertEqual(root.state.state_type.value, "VIEWPORT")

        root.open_overlay("status_screen")
        root.open_overlay("loadout_screen")
        self.assertEqual(root.state.open_overlay_id, "loadout_screen")

    def test_combat_updates_with_non_blocking_overlays(self):
        ticks = {"value": 0}

        def viewport_handler(_ev):
            ticks["value"] += 1
            return EventResult(consumed=True)

        root = build_default_ui_root(viewport_handler=viewport_handler)
        root.open_overlay("status_screen")
        self.assertFalse(root.is_viewport_suspended())

        root.dispatch_event(UIEvent(event_type="click", x=300, y=40))
        self.assertEqual(ticks["value"], 1)

    def test_blocking_system_menu_suspends_and_captures(self):
        ticks = {"value": 0}

        def viewport_handler(_ev):
            ticks["value"] += 1
            return EventResult(consumed=True)

        root = build_default_ui_root(viewport_handler=viewport_handler)
        root.dispatch_event(UIEvent(event_type="key", key="esc"))

        self.assertEqual(root.state.open_overlay_id, "system_menu")
        self.assertTrue(root.is_viewport_suspended())

        root.dispatch_event(UIEvent(event_type="click", x=300, y=40))
        self.assertEqual(ticks["value"], 0)

    def test_non_blocking_overlay_interactive_hits_consume(self):
        ticks = {"value": 0}

        def viewport_handler(_ev):
            ticks["value"] += 1
            return EventResult(consumed=True)

        root = build_default_ui_root(viewport_handler=viewport_handler)
        root.open_overlay("status_screen")

        root.dispatch_event(UIEvent(event_type="click", x=20, y=32))
        self.assertEqual(ticks["value"], 0)

        root.dispatch_event(UIEvent(event_type="click", x=220, y=40))
        self.assertEqual(ticks["value"], 1)


    def test_pixel_interface_art_renders_overlay_content(self):
        root = build_default_ui_root()
        root.open_overlay("status_screen")
        art = render_pixel_interface_art(root)

        self.assertIn("SERA PIXEL UI PREVIEW", art)
        self.assertIn("[ STATUS ]", art)
        self.assertIn("active=status_screen", art)

    def test_esc_back_behavior(self):
        root = build_default_ui_root()
        root.open_overlay("log_screen")
        root.dispatch_event(UIEvent(event_type="key", key="esc"))
        self.assertEqual(root.state.state_type.value, "VIEWPORT")

        root.dispatch_event(UIEvent(event_type="key", key="esc"))
        self.assertEqual(root.state.open_overlay_id, "system_menu")


if __name__ == "__main__":
    unittest.main()
