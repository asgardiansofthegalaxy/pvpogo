from unittest import TestCase

from pypogo.moves import Move, MoveKind
from pypogo.pokemon import Pokemon
from pypogo.tests.utils import load_bulbasaur


class PokemonTests(TestCase):
    def setUp(self) -> None:
        self.bulbasaur = load_bulbasaur()

    def test_pokemon_attributes(self):
        # Test the attributes of the Pokemon instance
        self.assertEqual(self.bulbasaur.pdex_mon.species_name, "Bulbasaur")
        self.assertEqual(self.bulbasaur.level, 50)
        self.assertEqual(self.bulbasaur.ivs.attack, 15)
        self.assertEqual(self.bulbasaur.ivs.defense, 15)
        self.assertEqual(self.bulbasaur.ivs.stamina, 15)

    def test_pokemon_cp(self):
        # Test the cp property of the Pokemon instance
        expected_cp = 1260
        self.assertEqual(self.bulbasaur.cp, expected_cp)

    def test_pokemon_hp(self):
        # Test the hp property of the Pokemon instance
        expected_hp = 120
        self.assertEqual(self.bulbasaur.hp, expected_hp)

    def test_pokemon_is_alive(self):
        # Test the is_alive method of the Pokemon instance
        self.assertTrue(self.bulbasaur.is_alive)

    def test_pokemon_get_move(self):
        # Test the get_move method of the Pokemon instance
        move_type = MoveKind.FAST  # Replace with the desired move type
        move = self.bulbasaur.get_move(move_type)
        self.assertIsInstance(move, Move)
        self.assertTrue(move.is_fast)

    def test_pokemon_to_from_dict(self):
        # Test the to_dict and from_dict methods of the Pokemon instance
        pokemon_dict = self.bulbasaur.to_dict()
        self.assertIsInstance(pokemon_dict, dict)

        # Test the from_dict method by creating a new Pokemon instance
        new_pokemon = Pokemon.from_dict(pokemon_dict)
        self.assertIsInstance(new_pokemon, Pokemon)

        # Test that the attributes of the new Pokemon instance match the original Pokemon instance
        self.assertEqual(new_pokemon.pdex_mon, self.bulbasaur.pdex_mon)
        self.assertEqual(new_pokemon.level, self.bulbasaur.level)
        self.assertEqual(new_pokemon.ivs.attack, self.bulbasaur.ivs.attack)
        self.assertEqual(new_pokemon.ivs.defense, self.bulbasaur.ivs.defense)
        self.assertEqual(new_pokemon.ivs.stamina, self.bulbasaur.ivs.stamina)
        self.assertEqual(
            new_pokemon.fast_move.move_id, self.bulbasaur.fast_move.move_id
        )
        self.assertEqual(
            new_pokemon.charged_moves[0].move_id,
            self.bulbasaur.charged_moves[0].move_id,
        )
