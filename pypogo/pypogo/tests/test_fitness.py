"""
Tests for the AI fitness benchmark.

The benchmark exists so AI changes can be argued with a number, which only
works if the number is trustworthy. Two properties carry all the weight and are
what these tests protect:

* An AI scored against a copy of itself must come out at exactly 500. That is
  what makes the distance from 500 a margin rather than an arbitrary reading,
  and it fails the moment the seat swap or the rating maths is wrong.
* The same AI over the same suite must produce the same number twice. It did
  not before `PvPokeAI` got its own RNG: scores moved by ~30 rating points run
  to run, more than separates the four tiers.

Deliberately *not* asserted: the ordering of the tiers. Measured over 28
pairings they sit within about one standard error of each other, so pinning an
order would be pinning noise. `scripts/ai_fitness.py` is where that gets looked
at, with the spread printed beside the scores.
"""

from unittest import TestCase

from pypogo.ai.fitness import (
    EVEN,
    build_suite,
    league_meta,
    play,
    score_ai,
    team_rating,
)
from pypogo.ai.naive import NaiveAI
from pypogo.ai.pvpoke.constants import AILevel
from pypogo.ai.pvpoke.pvpoke import PvPokeAI
from pypogo.battle import OneVsOneBattle
from pypogo.game_master.game_master import GameMaster
from pypogo.player import Player

GM = GameMaster()

#: Three teams -- three pairings, six battles -- which is the smallest suite
#: that still exercises more than one matchup. The gate pays about a second for
#: it; the real measurement is the script.
SUITE = build_suite(league_meta("great"), teams=3)


def champion(player):
    return PvPokeAI(player, level=AILevel.CHAMPION)


#: Scored once and shared. A 3v3 with the heuristic AI is ~150ms a battle, so
#: the tests below read one run rather than each paying for their own.
CHAMPION_REPORT = score_ai(GM, champion, SUITE)


class AnchorTests(TestCase):
    def test_an_ai_scores_exactly_500_against_a_copy_of_itself(self):
        # Both battles in a pairing are the same battle when the two AIs match,
        # so the two ratings sum to 1000 and the mean is exact. Any seat or
        # team bias would show up here as a drift off 500.
        report = score_ai(GM, NaiveAI, SUITE, reference=NaiveAI)

        self.assertEqual(report.score, EVEN)
        self.assertEqual(report.battles, len(SUITE) * 2)

    def test_both_sides_of_one_battle_account_for_a_single_outcome(self):
        one, two = SUITE[0]
        rating_one, rating_two = play(GM, one, two, NaiveAI, NaiveAI)

        self.assertAlmostEqual(rating_one + rating_two, 1000, places=6)

    def test_team_rating_matches_the_one_v_one_rating_for_a_single_pokemon(self):
        # The team formula generalises OneVsOneBattle's. If the two ever
        # disagree there are two definitions of "battle rating" in the repo.
        attacker = GM.get_pokemon("azumarill", level=40)
        defender = GM.get_pokemon("registeel", level=40)

        expected = OneVsOneBattle.simulate(attacker, defender, 1, 1)

        self.assertEqual(int(team_rating([attacker], [defender])), expected)


class ReproducibilityTests(TestCase):
    def test_scoring_the_same_ai_twice_gives_the_same_number(self):
        # The regression guard for PvPokeAI's RNG. Before it had its own
        # stream, this varied by tens of rating points.
        again = score_ai(GM, champion, SUITE)

        self.assertEqual(again.score, CHAMPION_REPORT.score)
        self.assertEqual(
            [r.as_one for r in again.results],
            [r.as_one for r in CHAMPION_REPORT.results],
        )

    def test_two_seeded_ais_on_the_same_team_draw_the_same_stream(self):
        player = Player(team=[GM.get_pokemon("azumarill", level=40)])
        draws = [
            [PvPokeAI(player, level=AILevel.CHAMPION)._rng.random() for _ in range(3)]
            for _ in range(2)
        ]

        self.assertEqual(draws[0], draws[1])

    def test_an_unseeded_ai_is_still_free_to_be_unpredictable(self):
        # seed=None is the documented opt-out, so it has to actually opt out.
        # Asserted on the stream rather than on battle outcomes: a battle only
        # sometimes turns on a coin flip, which would make this flaky.
        player = Player(team=[GM.get_pokemon("azumarill", level=40)])
        draws = {
            tuple(
                PvPokeAI(player, level=AILevel.CHAMPION, seed=None)._rng.random()
                for _ in range(3)
            )
            for _ in range(4)
        }

        self.assertGreater(
            len(draws), 1, "seed=None should not produce a fixed stream"
        )


class MarginTests(TestCase):
    def test_the_heuristic_ai_beats_the_naive_one(self):
        report = CHAMPION_REPORT

        # Measured at ~50-90 points depending on suite size, against a standard
        # error of ~10. The bound is loose enough to survive a rebuilt meta and
        # tight enough that an AI change which throws the advantage away fails.
        self.assertGreater(
            report.edge,
            25,
            f"PvPokeAI scored {report.score:.1f} against NaiveAI; it was ~+60 "
            "when the benchmark was written",
        )
