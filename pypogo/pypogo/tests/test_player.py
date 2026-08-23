from unittest import TestCase

from pypogo.player import Player
from pypogo.tests.utils import load_team


class PlayerTests(TestCase):
    def setUp(self) -> None:
        self.team = load_team()
        self.player = Player(self.team)

    def test_active_pokemon(self):
        self.assertEqual(self.player._active_pokemon_idx, 0)
        self.assertEqual(self.player.active_pokemon, self.team[0])

    def test_has_switch_timer(self):
        self.assertFalse(self.player.has_switch_timer)
        self.player.start_switch_timer(10)
        self.assertTrue(self.player.has_switch_timer)

    def test_start_switch_timer(self):
        self.player.start_switch_timer(3)
        self.assertEqual(self.player.switch_timer, 3)
        self.assertTrue(self.player.has_switch_timer)

    def test_decrease_switch_timer(self):
        self.player.start_switch_timer(3)
        self.player.decrease_switch_timer(2)
        self.assertEqual(self.player.switch_timer, 1)

        # Can't go below 0
        self.player.decrease_switch_timer(2)
        self.assertEqual(self.player.switch_timer, 0)

    def test_can_switch(self):
        self.assertTrue(self.player.can_switch)

        self.player.start_switch_timer(10)
        self.assertFalse(self.player.can_switch)

    def test_has_cooldown(self):
        self.assertFalse(self.player.has_cooldown)

    def test_decrease_cooldown(self):
        self.player.active_pokemon.cooldown_turns = 3
        self.player.decrease_cooldown(2)
        self.assertEqual(self.player.active_pokemon.cooldown_turns, 1)

        # Can't go below 0
        self.player.decrease_cooldown(2)
        self.assertEqual(self.player.active_pokemon.cooldown_turns, 0)

    def test_increase_cooldown(self):
        self.player.active_pokemon.cooldown_turns = 3
        self.player.increase_cooldown(2)
        self.assertEqual(self.player.active_pokemon.cooldown_turns, 5)

    def test_get_cooldown(self):
        self.player.active_pokemon.cooldown_turns = 3
        self.assertEqual(self.player.get_cooldown(), 3)
        self.assertTrue(self.player.has_cooldown)

    def test_is_active_alive(self):
        self.assertTrue(self.player.is_active_alive)

    def test_increase_energy(self):
        self.player.increase_energy(10)
        self.assertEqual(self.player.active_pokemon.energy, 10)

    def test_decrease_energy(self):
        self.player.active_pokemon.energy = 10
        self.player.decrease_energy(5)
        self.assertEqual(self.player.active_pokemon.energy, 5)

    def test_receive_damage(self):
        self.player.active_pokemon.hp = 100
        self.player.receive_damage(20)
        self.assertEqual(self.player.active_pokemon.hp, 80)

        # Damage can't go below 0
        self.player.receive_damage(100)
        self.assertEqual(self.player.active_pokemon.hp, 0)

    def test_get_remaining_pokemon(self):
        self.assertEqual(self.player.get_remaining_pokemon(), 3)
        self.player.active_pokemon.hp = 0
        self.assertEqual(self.player.get_remaining_pokemon(), 2)

    def test_use_shield(self):
        self.player._shields = 2
        self.player.use_shield()
        self.assertEqual(self.player._shields, 1)
        self.player.use_shield()
        self.assertEqual(self.player._shields, 0)

        # Shield count can't go below 0
        self.player.use_shield()
        self.assertEqual(self.player._shields, 0)

    def test_do_switch(self):
        self.assertEqual(len(self.player.team), 3)
        self.assertEqual(self.player._active_pokemon_idx, 0)

        self.player.do_switch(first_available=True)
        self.assertEqual(self.player._active_pokemon_idx, 1)

        self.player.do_switch(first_available=False)
        self.assertEqual(self.player._active_pokemon_idx, 2)
