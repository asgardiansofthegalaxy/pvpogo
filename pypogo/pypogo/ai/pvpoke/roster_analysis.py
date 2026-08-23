import sys
from typing import List

from pypogo.ai.pvpoke.constants import RosterPerformance, Scenario, ScenarioType
from pypogo.battle import OneVsOneBattle
from pypogo.constants import STARTING_SHIELDS
from pypogo.pokemon import PvpPokemon


class RosterAnalyzer:

    @staticmethod
    def run_scenario(
        name: ScenarioType, attacker: PvpPokemon, defender: PvpPokemon
    ) -> Scenario:
        """
        Runs a scenario between the player's active Pokemon and the opponent's active Pokemon.

        Args:
            name (ScenarioType): The type of scenario to run.
            attacker (PvpPokemon): The attacking pokemon.
            defender (PvpPokemon): The defending pokemon.

        Returns:
            Scenario: The result of the scenario, including matchups and average rating.

        Note:
            `name` currently only labels the result. The bait/no-bait
            distinction it is meant to draw needs shield baiting in the battle
            engine, which is not modelled yet, so all four ScenarioTypes
            produce identical numbers. `SCENARIO_TYPES` in constants.py is the
            config this would read once baiting exists.
        """
        scenario = Scenario(
            name=name,
            opponent=defender,
            matchups=[],
            average=0,
            min_shields=sys.maxsize,
        )
        attacker = attacker.clone()
        defender = defender.clone()

        shield_weights = [4, 4, 1]
        total_weight = 0

        for n_shields_atk in range(STARTING_SHIELDS + 1):
            for n_shields_def in range(STARTING_SHIELDS + 1):

                rating = OneVsOneBattle.simulate(
                    attacker, defender, n_shields_atk, n_shields_def
                )

                scenario.matchups.append(rating)
                shield_weight = (
                    shield_weights[n_shields_atk] * shield_weights[n_shields_def]
                )
                total_weight += shield_weight
                scenario.average += rating * shield_weight
                attacker.full_reset()
                defender.full_reset()

                if rating >= 500 and n_shields_atk < scenario.min_shields:
                    scenario.min_shields = n_shields_atk

        scenario.average /= total_weight

        return scenario

    @staticmethod
    def calculate_roster_performance(
        team_one: List[PvpPokemon], team_two: List[PvpPokemon]
    ) -> List[RosterPerformance]:
        """
        Calculates the average performance of team one against team two.

        Args:
            team_one (List[PvpPokemon]): The first team roster.
            team_two (List[PvpPokemon]): The second team roster.

        Returns:
            List[RosterPerformance]: A list of RosterPerformance objects, sorted by average rating in descending order.
        """
        results = []

        for pokemon in team_one:
            scenarios = RosterAnalyzer.run_bulk_scenarios(
                ScenarioType.NO_BAIT, pokemon, team_two
            )
            average = sum(scenario.average for scenario in scenarios) / len(scenarios)
            results.append(RosterPerformance(pokemon, scenarios, average))

        # Sort by average rating in descending order
        results.sort(key=lambda x: x.average, reverse=True)
        return results

    @staticmethod
    def run_bulk_scenarios(
        scenario_type: ScenarioType,
        attacker: PvpPokemon,
        team_two: List[PvpPokemon],
    ):
        """
        Runs multiple scenarios for a given attacker against a team of defenders.

        Args:
            scenario_type (ScenarioType): The type of scenario to run.
            attacker (Pokemon): The attacker Pokemon.
            team_two (List[PvpPokemon]): The team of defender Pokemon.

        Returns:
            List: A list of scenarios against each defender Pokemon.
        """
        scenarios = []

        for defender in team_two:
            scenario = RosterAnalyzer.run_scenario(scenario_type, attacker, defender)
            scenarios.append(scenario)

        return scenarios
