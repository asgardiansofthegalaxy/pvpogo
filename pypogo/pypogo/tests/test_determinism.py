"""
Battles must give the same answer twice.

Every precomputed artefact in this repo -- the matchup matrices, the roster
numbers quoted in docs -- is only meaningful if re-running the simulation
reproduces it. That was not true until the charge-move-priority tie-break
stopped reseeding the process-wide RNG from the wall clock: identical mirror
matches came out 481 or 518 depending on when they ran, and a `--check` drift
gate over such data would fail at random.

These tests pin the properties that make precomputation legitimate.
"""

import random
from unittest import TestCase

from pypogo.ai.pvpoke.constants import ScenarioType
from pypogo.ai.pvpoke.roster_analysis import RosterAnalyzer
from pypogo.battle import OneVsOneBattle, PvpBattle
from pypogo.game_master.game_master import GameMaster
from pypogo.player import Player

GM = GameMaster()


def _azumarill():
    return GM.get_pokemon("azumarill", "BUBBLE", ["PLAY_ROUGH", "ICE_BEAM"], level=41.5)


def _medicham():
    return GM.get_pokemon("medicham", "COUNTER", ["ICE_PUNCH", "PSYCHIC"], level=41.5)


def _slowbro():
    return GM.get_pokemon("slowbro", level=40)


def _slowking():
    return GM.get_pokemon("slowking", level=40)


class DeterminismTests(TestCase):
    def test_the_same_matchup_rates_the_same_every_time(self):
        ratings = {
            OneVsOneBattle.simulate(_azumarill(), _azumarill(), 1, 1) for _ in range(8)
        }
        self.assertEqual(
            len(ratings),
            1,
            f"a mirror match produced {sorted(ratings)}; battles must be reproducible "
            "for precomputed analysis to mean anything",
        )

    def test_reusing_pokemon_with_full_reset_matches_building_fresh_ones(self):
        fresh = OneVsOneBattle.simulate(_azumarill(), _medicham(), 1, 1)

        attacker, defender = _azumarill(), _medicham()
        OneVsOneBattle.simulate(attacker, defender, 1, 1)
        attacker.full_reset()
        defender.full_reset()
        reused = OneVsOneBattle.simulate(attacker, defender, 1, 1)

        self.assertEqual(fresh, reused, "full_reset() must restore a Pokemon completely")

    def test_a_battle_does_not_disturb_the_global_random_stream(self):
        # The tie-break used to call random.seed() on the module-level RNG,
        # which silently reset the stream PvPokeAI draws its energy guesses
        # from.
        random.seed(1234)
        expected = [random.random() for _ in range(3)]

        random.seed(1234)
        OneVsOneBattle.simulate(_azumarill(), _azumarill(), 1, 1)
        after = [random.random() for _ in range(3)]

        self.assertEqual(expected, after)

    def test_the_cmp_seed_is_what_decides_a_tie(self):
        # Slowbro and Slowking have identical attack at level 40, so charge
        # move priority between them comes down to the tie-break. Different
        # seeds must be able to reach different outcomes, or it has stopped
        # being a coin flip at all.
        outcomes = set()
        for seed in range(10):
            attacker = _slowbro()
            battle = PvpBattle(
                Player([attacker], shields=1),
                Player([_slowking()], shields=1),
                cmp_seed=seed,
            )
            battle.simulate()
            outcomes.add(attacker.hp)

        self.assertGreater(len(outcomes), 1, "cmp_seed no longer affects the tie-break")

    def test_a_tie_resolves_the_same_way_whichever_side_a_pokemon_starts_on(self):
        # The rating splits one battle between two sides, so rating(a vs b)
        # and rating(b vs a) must sum to 1000. They did not while the tie-break
        # was seeded per battle: whoever was player one won every tie, so both
        # sides won their own simulation.
        forward = OneVsOneBattle.simulate(_slowbro(), _slowking(), 1, 1)
        reverse = OneVsOneBattle.simulate(_slowking(), _slowbro(), 1, 1)

        self.assertAlmostEqual(
            forward + reverse,
            1000,
            delta=2,
            msg=f"{forward} + {reverse} should account for one battle, not two "
            "different ones",
        )

    def test_a_pokemon_rates_about_even_against_a_copy_of_itself(self):
        # A true mirror has no pair to tell apart, so ties alternate rather
        # than always falling to player one -- otherwise the attacker wins
        # every charged-move collision and a mirror reads as a losing matchup.
        #
        # This is a property of the shield-weighted sweep, not of a single
        # game: one battle has one decisive collision and somebody wins it.
        for species_id in ("azumarill", "medicham", "registeel"):
            with self.subTest(species=species_id):
                scenario = RosterAnalyzer.run_scenario(
                    ScenarioType.NO_BAIT,
                    GM.get_pokemon(species_id, level=40),
                    GM.get_pokemon(species_id, level=40),
                )
                self.assertAlmostEqual(scenario.rating, 500, delta=60)

    def test_an_unseeded_battle_still_runs(self):
        # cmp_seed=None is the escape hatch for callers that want the live
        # game's unpredictability rather than reproducibility.
        attacker, defender = _azumarill(), _medicham()
        battle = PvpBattle(
            Player([attacker], shields=1), Player([defender], shields=1), cmp_seed=None
        )
        battle.simulate()
        self.assertGreaterEqual(attacker.hp, 0)


class SingleChargedMoveTests(TestCase):
    """61 species declare one charged move; they used to crash mid-battle."""

    def test_a_pokemon_with_one_charged_move_can_battle(self):
        caterpie = GM.get_pokemon("caterpie", level=20)
        self.assertEqual(len(caterpie.charged_moves), 1)

        rating = OneVsOneBattle.simulate(caterpie, _azumarill(), 1, 1)
        self.assertGreaterEqual(rating, 0)
        self.assertLessEqual(rating, 1000)

    def test_every_species_the_dataset_can_build_survives_a_battle(self):
        # A sample rather than all 1,279, to keep the gate fast. The point is
        # that no move-pool shape in the dataset crashes the action rules.
        species = sorted(GM.pokedex)
        for species_id in species[:: len(species) // 30]:
            try:
                mon = GM.get_pokemon(species_id, level=20)
            except ValueError:
                continue  # documented gaps, covered by test_dataset_invariants
            with self.subTest(species=species_id):
                OneVsOneBattle.simulate(mon, _azumarill(), 1, 1)
