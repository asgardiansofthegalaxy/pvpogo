from unittest import TestCase

from pypogo.poketypes import PokeType


class PokeTypeTests(TestCase):
    def test_is_weak(self):
        # Test not weak against bug type
        self.assertFalse(PokeType.FIRE.is_weak(PokeType.BUG))
        # Test weak against water type
        self.assertTrue(PokeType.FIRE.is_weak(PokeType.WATER))

    def test_resists(self):
        # Test resists against grass type
        self.assertTrue(PokeType.FIRE.resists(PokeType.GRASS))
        # Test not resists against electric type
        self.assertFalse(PokeType.FIRE.resists(PokeType.ELECTRIC))

    def test_is_immunte(self):
        # Test immune to normal type
        self.assertTrue(PokeType.GHOST.is_immunte(PokeType.NORMAL))
        # Test not immune to psychic type
        self.assertFalse(PokeType.GHOST.is_immunte(PokeType.PSYCHIC))
