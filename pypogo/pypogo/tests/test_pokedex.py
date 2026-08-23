import json
from unittest import TestCase

from pypogo.pokedex import PokedexEntry
from pypogo.regions import KANTO_REGION
from pypogo.tests.utils import load_bulbasaur_data


class PokedexEntryTests(TestCase):
    def setUp(self) -> None:
        self.bulbasaur_json = load_bulbasaur_data()
        self.bulbasaur = PokedexEntry.from_dict(self.bulbasaur_json)

    def test_from_to_json(self):
        pokemon = PokedexEntry.from_dict(self.bulbasaur_json)
        json_data = pokemon.to_json()
        self.assertEqual(json_data, json.dumps(self.bulbasaur_json))

    def test_get_region(self):
        self.assertEqual(self.bulbasaur.region, KANTO_REGION)

    def test_is_starter(self):
        self.assertTrue(self.bulbasaur.is_starter())

    def test_is_regional(self):
        self.assertFalse(self.bulbasaur.is_regional())
