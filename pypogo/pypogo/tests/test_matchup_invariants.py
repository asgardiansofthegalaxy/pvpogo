"""
Invariants the precomputed matchup files must satisfy.

These files are the first artefact in the repo produced by *simulation* rather
than transcription, which makes them the easiest thing to ship quietly broken:
a rebuild against a changed engine can shift every number without changing the
shape. These checks are the ones that would catch that -- referential
integrity against the dataset, ratings in range, a complete matrix, and two
properties that only hold if the simulation itself is sound:

* a mirror match must rate near 500, because a Pokemon fighting an identical
  copy of itself deals and takes the same damage;
* rating(a vs b) and rating(b vs a) must sum to 1000, because the rating splits
  damage dealt and HP retained between the two sides.

Both held to within a point when the files were generated. They are not
tautologies: a build with inconsistent movesets between rows and columns broke
the first, and a nondeterministic tie-break broke both.
"""

import json
from pathlib import Path
from statistics import mean
from unittest import TestCase

from pypogo.game_master.game_master import CWD, GameMaster
from pypogo.meta import (
    LEAGUE_IVS,
    LEAGUE_KEYS,
    MAX_FORMS_PER_DEX,
    matchups_filename,
    mechanical_signature,
)
from pypogo.movesets import ENERGY_BUDGET

GM = GameMaster()


def _load(league):
    path = Path(CWD) / matchups_filename(league)
    if not path.exists():
        raise AssertionError(
            f"{path.name} is missing. Rebuild it with:\n"
            f"  cd pypogo && python3 pypogo/scripts/build_matchups.py --league {league}"
        )
    return json.loads(path.read_text())


LEAGUES = {league: _load(league) for league in sorted(LEAGUE_KEYS)}


class ShapeTests(TestCase):
    def test_every_league_ships_a_file(self):
        self.assertEqual(sorted(LEAGUES), sorted(LEAGUE_KEYS))

    def test_the_matrix_is_complete(self):
        for league, data in LEAGUES.items():
            width = len(data["meta"])
            for species_id, ratings in data["ratings"].items():
                with self.subTest(league=league, species=species_id):
                    self.assertEqual(
                        len(ratings), width, "every row must cover every meta pick"
                    )

    def test_ratings_are_in_range(self):
        for league, data in LEAGUES.items():
            for species_id, ratings in data["ratings"].items():
                with self.subTest(league=league, species=species_id):
                    self.assertTrue(
                        all(0 <= r <= 1000 for r in ratings),
                        f"ratings out of the 0-1000 range: {sorted(ratings)[:3]}",
                    )

    def test_the_meta_is_a_sane_size(self):
        for league, data in LEAGUES.items():
            with self.subTest(league=league):
                self.assertGreaterEqual(len(data["meta"]), 20)
                self.assertEqual(
                    len(data["meta"]),
                    len({m["id"] for m in data["meta"]}),
                    "a species appears in the meta twice",
                )

    def test_no_species_floods_the_meta_with_its_forms(self):
        for league, data in LEAGUES.items():
            counts: dict[int, int] = {}
            for entry in data["meta"]:
                dex = GM.pokedex[entry["id"]].dex_number
                counts[dex] = counts.get(dex, 0) + 1
            for dex, count in counts.items():
                with self.subTest(league=league, dex=dex):
                    self.assertLessEqual(count, MAX_FORMS_PER_DEX)


class ReferentialIntegrityTests(TestCase):
    def test_every_species_referenced_exists_in_the_dataset(self):
        for league, data in LEAGUES.items():
            referenced = set(data["ratings"]) | {m["id"] for m in data["meta"]}
            referenced |= set(data["aliases"]) | set(data["aliases"].values())
            for species_id in referenced:
                with self.subTest(league=league, species=species_id):
                    self.assertIn(species_id, GM.pokedex)

    def test_every_meta_pick_has_its_own_row(self):
        for league, data in LEAGUES.items():
            for entry in data["meta"]:
                with self.subTest(league=league, species=entry["id"]):
                    self.assertIn(entry["id"], data["ratings"])

    def test_every_build_uses_moves_the_species_actually_has(self):
        for league, data in LEAGUES.items():
            for species_id, build in data["builds"].items():
                entry = GM.pokedex[species_id]
                with self.subTest(league=league, species=species_id):
                    self.assertIn(build["fast"], entry.fast_moves)
                    for move_id in build["charged"]:
                        self.assertIn(move_id, entry.charged_moves)
                    self.assertTrue(GM.moves[build["fast"]].is_fast)

    def test_every_build_is_legal_for_its_league(self):
        for league, data in LEAGUES.items():
            for species_id, build in data["builds"].items():
                with self.subTest(league=league, species=species_id):
                    self.assertLessEqual(build["cp"], data["cap"])
                    self.assertGreaterEqual(build["level"], 1)
                    self.assertLessEqual(build["level"], 50)

    def test_aliases_point_at_a_rated_and_identical_species(self):
        for league, data in LEAGUES.items():
            for member, representative in data["aliases"].items():
                with self.subTest(league=league, species=member):
                    self.assertNotIn(member, data["ratings"], "an alias has its own row")
                    self.assertIn(representative, data["ratings"])
                    self.assertEqual(
                        mechanical_signature(GM.pokedex[member]),
                        mechanical_signature(GM.pokedex[representative]),
                        "an alias must battle identically to its representative",
                    )

    def test_the_recorded_assumptions_match_the_code_that_built_them(self):
        # If someone retunes the move ranking or the IV spread without
        # rebuilding, the shipped numbers describe Pokemon the code no longer
        # produces.
        for league, data in LEAGUES.items():
            with self.subTest(league=league):
                self.assertEqual(data["assumptions"]["ivs"], LEAGUE_IVS.to_dict())
                self.assertEqual(
                    data["assumptions"]["energy_budget"], ENERGY_BUDGET
                )
                self.assertEqual(data["cap"], LEAGUE_KEYS[league].value)


class SimulationSanityTests(TestCase):
    """Properties that hold only if the underlying battles are sound."""

    def test_mirror_matches_are_centred_on_even(self):
        """
        A species against a copy of itself should be a coin flip.

        Not exactly 500 per species: a battle contains a handful of decisive
        charged-move collisions and somebody has to win each, so an individual
        mirror lands within about a hundred points either way. What must hold
        is that they are *centred* -- when the tie-break was seeded per battle,
        player one won every collision and every mirror sat above 500.
        """
        for league, data in LEAGUES.items():
            mirrors = [
                data["ratings"][entry["id"]][index]
                for index, entry in enumerate(data["meta"])
            ]
            above = sum(1 for m in mirrors if m > 500)

            with self.subTest(league=league):
                self.assertAlmostEqual(
                    mean(mirrors),
                    500,
                    delta=25,
                    msg=f"mirror ratings average {mean(mirrors):.0f}, which means the "
                    "tie-break favours one side of the battle",
                )
                self.assertGreater(
                    above,
                    len(mirrors) // 4,
                    "almost every mirror lost; the tie-break is biased",
                )
                self.assertLess(
                    above,
                    len(mirrors) * 3 // 4,
                    "almost every mirror won; the tie-break is biased",
                )
                self.assertLess(
                    max(abs(m - 500) for m in mirrors),
                    150,
                    f"a mirror rated {min(mirrors)}..{max(mirrors)}; that is further "
                    "from even than turn discreteness explains",
                )

    def test_opposing_ratings_sum_to_a_thousand(self):
        for league, data in LEAGUES.items():
            index_of = {m["id"]: i for i, m in enumerate(data["meta"])}
            ids = list(index_of)
            for i, a in enumerate(ids):
                for b in ids[i + 1 :]:
                    total = data["ratings"][a][index_of[b]] + data["ratings"][b][index_of[a]]
                    with self.subTest(league=league, pair=(a, b)):
                        self.assertAlmostEqual(
                            total,
                            1000,
                            delta=3,
                            msg=f"{a} vs {b} rated {total} in total; the rating "
                            "splits one battle between two sides and must sum to 1000",
                        )

    def test_the_meta_is_stronger_than_the_field(self):
        # The meta is defined as the species that win, so its members should
        # average better against it than a random slice of the dex does.
        for league, data in LEAGUES.items():
            meta_ids = [m["id"] for m in data["meta"]]
            meta_mean = sum(
                sum(data["ratings"][s]) / len(data["ratings"][s]) for s in meta_ids
            ) / len(meta_ids)

            everyone = sorted(data["ratings"])
            field = everyone[:: max(1, len(everyone) // 200)]
            field_mean = sum(
                sum(data["ratings"][s]) / len(data["ratings"][s]) for s in field
            ) / len(field)

            with self.subTest(league=league):
                self.assertGreater(meta_mean, field_mean + 50)
