"""
Invariants the derived dataset must satisfy.

These are what make regenerating the dataset a safe, unattended operation: a
rebuild that violates any of them fails the gate instead of silently shipping a
broken roster. They check internal consistency, not agreement with any external
source, so they stay meaningful as the game changes.
"""

import json
from pathlib import Path
from unittest import TestCase

from pypogo.constants import MAX_STAT
from pypogo.game_master.game_master import CWD, MOVES_FILE, POKEDEX_FILE, GameMaster
from pypogo.moves import Move
from pypogo.pokedex import PokedexEntry
from pypogo.poketypes import PokeType

SPECIES = json.loads((Path(CWD) / POKEDEX_FILE).read_text())

# Known gaps in the upstream export, pinned so they cannot quietly grow. Each
# is a real quirk of the source data, not a bug in the derivation.

#: Datamined ahead of release, so the export carries no stats for them yet.
UNRELEASED_NO_STATS = {"honedge", "doublade", "aegislash"}

#: Smeargle's moveset comes from Sketch, so it has no fixed pool to declare.
NO_FIXED_MOVESET = {"smeargle"}

#: Struggle is a charged move that the export nonetheless lists under
#: quickMoves for a handful of species that were never battle-implemented.
FAST_POOL_EXCEPTIONS = {("STRUGGLE",)}
MOVES = json.loads((Path(CWD) / MOVES_FILE).read_text())
MOVES_BY_ID = {entry["move_id"]: entry for entry in MOVES.values()}


class MoveTableTests(TestCase):
    def test_move_ids_are_unique(self):
        self.assertEqual(
            len(MOVES_BY_ID),
            len(MOVES),
            "Two moves share a move_id, so one would shadow the other when the "
            "engine re-keys the table.",
        )

    def test_every_move_parses(self):
        for key, entry in MOVES.items():
            with self.subTest(move=key):
                self.assertIsInstance(Move.from_dict(entry), Move)

    def test_move_types_are_known(self):
        for key, entry in MOVES.items():
            with self.subTest(move=key):
                PokeType(entry["move_type"])  # raises on an unknown type

    def test_fast_moves_generate_energy_and_charged_moves_spend_it(self):
        for key, entry in MOVES.items():
            with self.subTest(move=key):
                if entry["is_fast"]:
                    self.assertGreaterEqual(entry["energy_gain"], 0)
                    self.assertEqual(
                        entry["energy"], 0, "a fast move should not cost energy"
                    )
                else:
                    self.assertGreater(
                        entry["energy"], 0, "a charged move must cost energy"
                    )

    def test_move_values_are_in_range(self):
        for key, entry in MOVES.items():
            with self.subTest(move=key):
                self.assertGreaterEqual(entry["power"], 0)
                self.assertGreater(
                    entry["cooldown"], 0, "a zero cooldown would divide by zero"
                )
                self.assertEqual(
                    entry["cooldown"] % 500,
                    0,
                    "durations are whole 500ms battle turns",
                )


class SpeciesTableTests(TestCase):
    def test_every_species_parses(self):
        for species_id, entry in SPECIES.items():
            with self.subTest(species=species_id):
                self.assertIsInstance(PokedexEntry.from_dict(entry), PokedexEntry)

    def test_species_ids_match_their_keys(self):
        for species_id, entry in SPECIES.items():
            with self.subTest(species=species_id):
                self.assertEqual(entry["species_id"], species_id)

    def test_base_stats_are_plausible(self):
        for species_id, entry in SPECIES.items():
            if species_id in UNRELEASED_NO_STATS:
                continue
            with self.subTest(species=species_id):
                for stat, value in entry["base_stats"].items():
                    self.assertGreater(value, 0, f"{stat} must be positive")
                    self.assertLessEqual(value, MAX_STAT, f"{stat} out of range")

    def test_the_set_of_statless_species_has_not_grown(self):
        statless = {
            sid
            for sid, entry in SPECIES.items()
            if all(v == 0 for v in entry["base_stats"].values())
        }

        self.assertEqual(
            statless,
            UNRELEASED_NO_STATS,
            "The set of species missing base stats changed. If the export now "
            "covers one, drop it from UNRELEASED_NO_STATS; if a new one appeared, "
            "confirm it is genuinely unreleased before pinning it.",
        )

    def test_typings_are_known_and_non_empty(self):
        for species_id, entry in SPECIES.items():
            with self.subTest(species=species_id):
                types = entry["types"]
                self.assertTrue(types, "a species needs at least one type")
                for type_name in types:
                    PokeType(type_name)  # raises on an unknown type

    def test_dex_numbers_are_positive(self):
        for species_id, entry in SPECIES.items():
            with self.subTest(species=species_id):
                self.assertGreater(entry["dex_number"], 0)


class ReferentialIntegrityTests(TestCase):
    """The invariant that actually breaks battles when a rebuild goes wrong."""

    def test_every_species_move_resolves_to_a_real_move(self):
        dangling = []
        for species_id, entry in SPECIES.items():
            for move_id in entry["fast_moves"] + entry["charged_moves"]:
                if move_id not in MOVES_BY_ID:
                    dangling.append(f"{species_id} -> {move_id}")

        self.assertEqual(
            dangling, [], f"species reference moves that do not exist: {dangling[:10]}"
        )

    def test_every_species_has_a_usable_moveset(self):
        # The engine picks fast_moves[0] and charged_moves[:2] when a caller
        # does not specify, so an empty pool is an IndexError waiting to happen.
        for species_id, entry in SPECIES.items():
            if species_id in NO_FIXED_MOVESET:
                continue
            with self.subTest(species=species_id):
                self.assertTrue(entry["fast_moves"], "no fast moves")
                self.assertTrue(entry["charged_moves"], "no charged moves")

    def test_the_set_of_movesetless_species_has_not_grown(self):
        movesetless = {
            sid
            for sid, entry in SPECIES.items()
            if not entry["fast_moves"] or not entry["charged_moves"]
        }

        self.assertEqual(movesetless, NO_FIXED_MOVESET)

    def test_declared_fast_and_charged_pools_hold_the_right_kind_of_move(self):
        mismatched = []
        allowed_in_fast_pool = {m for group in FAST_POOL_EXCEPTIONS for m in group}
        for species_id, entry in SPECIES.items():
            for move_id in entry["fast_moves"]:
                if move_id in allowed_in_fast_pool:
                    continue
                if not MOVES_BY_ID[move_id]["is_fast"]:
                    mismatched.append(f"{species_id}: {move_id} in fast pool")
            for move_id in entry["charged_moves"]:
                if MOVES_BY_ID[move_id]["is_fast"]:
                    mismatched.append(f"{species_id}: {move_id} in charged pool")

        self.assertEqual(mismatched, [], f"moveset kind mismatch: {mismatched[:10]}")


class EndToEndTests(TestCase):
    def test_game_master_builds_a_battle_ready_pokemon_from_the_dataset(self):
        gm = GameMaster()
        pokemon = gm.get_pokemon("azumarill", "BUBBLE", ["ICE_BEAM", "PLAY_ROUGH"], 45.5)

        self.assertEqual(pokemon.pdex_mon.species_name, "Azumarill")
        self.assertGreater(pokemon.cp, 0)
        self.assertGreater(pokemon.hp, 0)
        self.assertEqual(len(pokemon.charged_moves), 2)

    def test_unbuildable_species_raise_instead_of_returning_nonsense(self):
        gm = GameMaster()

        for species_id in sorted(UNRELEASED_NO_STATS | NO_FIXED_MOVESET):
            with self.subTest(species=species_id):
                with self.assertRaises(ValueError):
                    gm.get_pokemon(species_id)

    def test_a_sample_of_species_across_the_dex_all_build(self):
        gm = GameMaster()
        unbuildable = UNRELEASED_NO_STATS | NO_FIXED_MOVESET
        sample = [s for s in sorted(SPECIES) if s not in unbuildable]
        sample = sample[:: max(1, len(sample) // 40)]

        for species_id in sample:
            with self.subTest(species=species_id):
                pokemon = gm.get_pokemon(species_id)
                self.assertGreater(pokemon.hp, 0)
                self.assertTrue(pokemon.charged_moves)
