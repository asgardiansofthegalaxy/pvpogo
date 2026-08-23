from unittest import TestCase

from pypogo.ai.pvpoke.roster_analysis import RosterAnalyzer
from pypogo.ai.pvpoke.team_generation import TeamGenerator
from pypogo.ai.pvpoke.tests.fixtures import (
    load_all_fire_team,
    load_all_grass_team,
    load_all_water_team,
)


class TeamGeneratorTest(TestCase):
    def setUp(self):
        self.grass_team = load_all_grass_team()
        self.fire_team = load_all_fire_team()
        self.water_team = load_all_water_team()

    def test_calculate_roster_performance(self):
        # These figures come from the shield-weighted sweep that
        # RosterAnalyzer.run_scenario performs today: every attacker/defender
        # shield count from 0 to 2, weighted [4, 4, 1].
        #
        # The previous expectations (chikorita 848, treecko 803, snivy 768)
        # were recorded against an earlier version that rated a single
        # 0-shield-vs-0-shield matchup -- chikorita still scores exactly 848.3
        # under that older rule. Don't "restore" them without also changing
        # run_scenario back; the sweep is what produces Scenario.min_shields.

        # When
        performances = RosterAnalyzer.calculate_roster_performance(
            team_one=self.grass_team, team_two=self.water_team
        )

        # Then
        self.assertEqual(len(performances), 3)
        self.assertEqual(performances[0].pokemon.pdex_mon.species_id, "snivy")
        self.assertEqual(round(performances[0].average), 783)
        self.assertEqual(performances[1].pokemon.pdex_mon.species_id, "chikorita")
        self.assertEqual(round(performances[1].average), 777)
        self.assertEqual(performances[2].pokemon.pdex_mon.species_id, "treecko")
        self.assertEqual(round(performances[2].average), 732)

    def test_generate_best_team(self):
        # When
        best_team = TeamGenerator.generate_best_team(
            [*self.grass_team, *self.water_team, *self.fire_team], self.fire_team
        )

        # Then
        self.assertEqual(len(best_team), 3)
        team_species = sorted([mon.pdex_mon.species_id for mon in best_team])
        self.assertListEqual(team_species, ["froakie", "squirtle", "totodile"]),

    def test_generate_last_lead_counter_team(self):
        # When
        best_team = TeamGenerator.generate_last_lead_counter(
            [*self.grass_team, *self.water_team, *self.fire_team],
            self.grass_team,
            [[self.grass_team[2]]],  # treecko
        )

        # Then
        self.assertEqual(len(best_team), 3)
        team_species = sorted([mon.pdex_mon.species_id for mon in best_team])
        self.assertListEqual(team_species, ["charmander", "cyndaquil", "torchic"]),

    def test_generate_unbalanced_team(self):
        # When
        best_team = TeamGenerator.generate_unbalanced_team(
            [*self.grass_team, *self.water_team, *self.fire_team],
            self.grass_team,
        )

        # Then
        self.assertEqual(len(best_team), 3)
        team_species = sorted([mon.pdex_mon.species_id for mon in best_team])
        self.assertListEqual(team_species, ["charmander", "cyndaquil", "torchic"]),

    def test_generate_counter_team(self):
        # When
        best_team = TeamGenerator.generate_unbalanced_team(
            [*self.grass_team, *self.water_team, *self.fire_team],
            self.water_team,
        )

        # Then
        self.assertEqual(len(best_team), 3)
        team_species = sorted([mon.pdex_mon.species_id for mon in best_team])
        self.assertListEqual(team_species, ["chikorita", "snivy", "treecko"]),
