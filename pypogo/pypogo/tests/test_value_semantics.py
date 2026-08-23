"""
Regression tests for classes that define __eq__.

Defining __eq__ without __hash__ sets __hash__ to None, which silently makes
instances unusable as dict keys or set members. These enums and value objects
all hit that, and the enums additionally raised AttributeError when compared to
a plain int instead of returning False.
"""

from unittest import TestCase

from pypogo.action import PvpAction
from pypogo.ai.interface import AIStatus
from pypogo.constants import BattlePhase
from pypogo.pokedex import PokedexEntry, PokemonFamily
from pypogo.poketypes import PokeType
from pypogo.stats import Stats, StatsCombo


class EnumValueSemanticsTests(TestCase):
    MEMBERS = (
        BattlePhase.NEUTRAL,
        PvpAction.FAST,
        AIStatus.AI_SUCCESS,
    )

    def test_members_are_hashable(self):
        for member in self.MEMBERS:
            with self.subTest(member=member):
                self.assertIsInstance(hash(member), int)

    def test_members_work_as_dict_keys_and_set_elements(self):
        lookup = {member: member.name for member in self.MEMBERS}

        self.assertEqual(len(lookup), len(self.MEMBERS))
        self.assertEqual(len({PvpAction.FAST, PvpAction.FAST, PvpAction.WAIT}), 2)

    def test_comparing_to_a_non_member_is_false_not_an_error(self):
        for member in self.MEMBERS:
            with self.subTest(member=member):
                self.assertFalse(member == 1)
                self.assertFalse(member == "FAST")
                self.assertTrue(member != 1)

    def test_members_still_compare_equal_to_themselves(self):
        for member in self.MEMBERS:
            with self.subTest(member=member):
                self.assertEqual(member, member)

    def test_distinct_members_are_not_equal(self):
        self.assertNotEqual(BattlePhase.NEUTRAL, BattlePhase.GAME_OVER)
        self.assertNotEqual(PvpAction.FAST, PvpAction.WAIT)


class StatsComboEqualityTests(TestCase):
    def _combo(self, ivs: Stats) -> StatsCombo:
        return StatsCombo(level=40.0, base=Stats(100, 100, 100), ivs=ivs)

    def test_combos_with_different_stats_are_not_equal(self):
        # This used to return a 3-tuple of comparisons. A non-empty tuple is
        # always truthy, so every StatsCombo compared equal to every other.
        self.assertNotEqual(
            self._combo(Stats(15, 15, 15)), self._combo(Stats(0, 0, 0))
        )

    def test_combos_with_matching_stats_are_equal(self):
        self.assertEqual(
            self._combo(Stats(15, 15, 15)), self._combo(Stats(15, 15, 15))
        )

    def test_combos_are_hashable_and_dedupe_by_value(self):
        combos = {
            self._combo(Stats(15, 15, 15)),
            self._combo(Stats(15, 15, 15)),
            self._combo(Stats(0, 0, 0)),
        }

        self.assertEqual(len(combos), 2)


class PokedexEntryHashTests(TestCase):
    def _entry(self, dex_number: int, species_id: str) -> PokedexEntry:
        return PokedexEntry(
            dex_number=dex_number,
            species_name=species_id.title(),
            species_id=species_id,
            family=PokemonFamily(species_id.upper(), None, []),
            types=[PokeType("grass"), PokeType("none")],
            base_stats=Stats(100, 100, 100),
            tags=[],
            fast_moves=["VINE_WHIP"],
            charged_moves=["SEED_BOMB"],
            buddy_distance=3,
            third_move_cost=50000,
        )

    def test_entries_are_hashable_and_dedupe_by_identity_fields(self):
        entries = {
            self._entry(1, "bulbasaur"),
            self._entry(1, "bulbasaur"),
            self._entry(4, "charmander"),
        }

        self.assertEqual(len(entries), 2)

    def test_equal_entries_hash_alike(self):
        self.assertEqual(
            hash(self._entry(1, "bulbasaur")), hash(self._entry(1, "bulbasaur"))
        )
