import json
from unittest import TestCase

from pypogo.moves import Move
from pypogo.tests.utils import load_wrap


class MoveTests(TestCase):
    def setUp(self) -> None:
        self.wrap_data = load_wrap()

    def test_to_from_dict(self):
        move = Move.from_dict(self.wrap_data)
        move_json = move.to_json()
        print(self.wrap_data)
        print(move_json)
        self.assertEqual(move_json, json.dumps(self.wrap_data))
