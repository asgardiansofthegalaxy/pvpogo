"""
Tests for move ranking.

The scoring in `pypogo.movesets` is a heuristic standing in for brute-force
simulation, so the test that matters is the one that measures it against
simulation. `test_ranking_beats_the_datasets_own_move_order` does exactly that
on a fixed sample small enough to keep the gate fast; the numbers it pins came
from a wider 38-species sweep, recorded in the assertion messages.
"""

from unittest import TestCase

from pypogo.battle import OneVsOneBattle
from pypogo.game_master.game_master import GameMaster
from pypogo.movesets import (
    best_moveset,
    enumerate_movesets,
    rank_charged_moves,
    rank_fast_moves,
)

GM = GameMaster()

#: Opponents the sample is scored against. Fixed, so the measurement is
#: comparable run to run; small, so the whole test stays under a second.
PANEL = ("registeel", "azumarill", "medicham")

#: Which charged move sits in which slot does not change the outcome under
#: the default AI, so a moveset is keyed by its unordered pair.

#: Species with enough of a move pool for the choice to be interesting.
SAMPLE = ("azumarill", "medicham", "venusaur", "altaria", "swampert", "umbreon")

LEVEL = 40.0


def _mean_rating(species_id, fast, charged, panel):
    mon = GM.get_pokemon(species_id, fast, list(charged), level=LEVEL)
    total = 0
    for opponent in panel:
        total += OneVsOneBattle.simulate(mon, opponent, 1, 1)
        mon.full_reset()
        opponent.full_reset()
    return total / len(panel)


class MoveRankingTests(TestCase):
    def test_azumarill_does_not_lead_with_rock_smash(self):
        # The motivating case: the dataset lists Rock Smash first, and nothing
        # about Azumarill makes that the move it should be built with.
        entry = GM.pokedex["azumarill"]
        fast, _ = best_moveset(entry, GM.moves)
        self.assertEqual(fast, "BUBBLE")
        self.assertNotEqual(fast, entry.fast_moves[0])

    def test_energy_generation_can_outrank_damage(self):
        # Lock On does 1 damage. It is Registeel's best fast move because of
        # what its energy buys, which is the whole point of weighting energy
        # by the species' own best charged move.
        fast, _ = best_moveset(GM.pokedex["registeel"], GM.moves)
        self.assertEqual(fast, "LOCK_ON")

    def test_ranking_is_deterministic_and_total(self):
        entry = GM.pokedex["swampert"]
        first = [m.move_id for m in rank_charged_moves(entry, GM.moves)]
        second = [m.move_id for m in rank_charged_moves(entry, GM.moves)]
        self.assertEqual(first, second)
        self.assertEqual(sorted(first), sorted(entry.charged_moves))

    def test_fast_pool_ignores_charged_moves_listed_in_it(self):
        # The export files Struggle under quickMoves for a few species.
        for species_id, entry in GM.pokedex.items():
            fast_ids = {m.move_id for m in rank_fast_moves(entry, GM.moves)}
            for move_id in fast_ids:
                with self.subTest(species=species_id, move=move_id):
                    self.assertTrue(GM.moves[move_id].is_fast)

    def test_species_with_a_single_charged_move_still_resolves(self):
        # 61 species declare one charged move; best_moveset returns the one it
        # has rather than padding or failing.
        fast, charged = best_moveset(GM.pokedex["caterpie"], GM.moves)
        self.assertTrue(fast)
        self.assertEqual(len(charged), 1)

    def test_unusable_pools_raise_like_get_pokemon_does(self):
        with self.assertRaises(ValueError):
            best_moveset(GM.pokedex["smeargle"], GM.moves)


class MoveRankingQualityTests(TestCase):
    """The measurement that justifies shipping a heuristic at all."""

    def test_ranking_beats_the_datasets_own_move_order(self):
        panel = [GM.get_pokemon(s, level=LEVEL) for s in PANEL]

        heuristic_regret = []
        default_regret = []

        for species_id in SAMPLE:
            entry = GM.pokedex[species_id]
            scored = {
                (fast, tuple(sorted(charged))): _mean_rating(species_id, fast, charged, panel)
                for fast, charged in enumerate_movesets(entry, GM.moves)
            }
            best = max(scored.values())

            fast, charged = best_moveset(entry, GM.moves)
            heuristic_regret.append(best - scored[(fast, tuple(sorted(charged)))])

            default_fast = next(m for m in entry.fast_moves if GM.moves[m].is_fast)
            default_key = (default_fast, tuple(sorted(entry.charged_moves[:2])))
            if default_key in scored:
                default_regret.append(best - scored[default_key])

        heuristic_mean = sum(heuristic_regret) / len(heuristic_regret)
        default_mean = sum(default_regret) / len(default_regret)

        # Measured over 38 randomly sampled species: heuristic ~11 points of
        # regret against brute force, the dataset's own order ~47. The bound
        # here is loose enough to survive dataset updates and tight enough
        # that losing to the default order fails.
        self.assertLess(
            heuristic_mean,
            default_mean,
            f"ranking ({heuristic_mean:.1f}) should give up less rating than the "
            f"dataset's move order ({default_mean:.1f})",
        )
        self.assertLess(
            heuristic_mean,
            30,
            f"ranking gives up {heuristic_mean:.1f} rating points against brute "
            "force; it was ~11 when written",
        )
