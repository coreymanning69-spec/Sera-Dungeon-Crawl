import unittest

from sera.elements import is_adjacent, resistance_modifier
from sera.tags import DamageTag


class TestElementFramework(unittest.TestCase):
    def test_ring_adjacency(self):
        self.assertTrue(is_adjacent(DamageTag.FIRE, DamageTag.AIR))
        self.assertTrue(is_adjacent(DamageTag.FIRE, DamageTag.EARTH))
        self.assertFalse(is_adjacent(DamageTag.FIRE, DamageTag.WATER))

    def test_defensive_bias_vs_fire(self):
        self.assertGreater(
            resistance_modifier(DamageTag.FIRE, DamageTag.ICE),
            resistance_modifier(DamageTag.FIRE, DamageTag.WATER),
        )

    def test_opposites_cancel(self):
        self.assertEqual(resistance_modifier(DamageTag.ICE, DamageTag.FIRE), 0.0)


if __name__ == "__main__":
    unittest.main()
