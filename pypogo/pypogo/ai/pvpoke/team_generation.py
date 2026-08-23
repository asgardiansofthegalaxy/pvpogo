import random
from typing import List

from pypogo.ai.pvpoke.constants import ScenarioType
from pypogo.ai.pvpoke.roster_analysis import RosterAnalyzer
from pypogo.pokemon import PvpPokemon


class TeamGenerator:

    @staticmethod
    def generate_best_team(
        roster: List[PvpPokemon], opponent_roster: List[PvpPokemon]
    ) -> List[PvpPokemon]:
        """
        Generates the best team of Pokémon based on their performance against the opponent's roster.

        Args:
            roster: (List[PvpPokemon]): The roster of Pokémon.
            opponent_roster (List[PvpPokemon]): The opponent's roster of Pokémon.

        Returns:
            List[PvpPokemon]: The best team of Pokémon.
        """
        team = []

        # Calculate the average performance of each Pokémon in the roster against the opponent's roster
        team_performance = RosterAnalyzer.calculate_roster_performance(
            roster, opponent_roster
        )

        # Lead with the best average Pokémon
        team.append(team_performance[0].pokemon)

        # Analyze the lead Pokémon's scenarios to find its worst matchups (i.e., where it performs poorly)
        scenarios = sorted(team_performance[0].scenarios, key=lambda x: x.average)

        # Identify the top two opponents our lead struggles against
        targets = [scenarios[0].opponent, scenarios[1].opponent]

        # Recalculate our team's performance specifically against these targets
        team_performance_against_targets = RosterAnalyzer.calculate_roster_performance(
            roster, targets
        )

        # Find the best bodyguard (a Pokémon that performs well against our lead's counters) that isn't already selected
        for performance in team_performance_against_targets:
            if performance.pokemon not in team:
                # Randomly decide whether to lead with the bodyguard or place it in the back
                if random.random() > 0.5:
                    team.append(performance.pokemon)
                else:
                    team.insert(0, performance.pokemon)
                break

        # Finally, identify a Pokémon that best complements the first two against their collective counters
        # This involves looking at how the opponent's roster performs against our current team,
        # then selecting a Pokémon from our roster that performs best against those counters
        team_performance_against_team = RosterAnalyzer.calculate_roster_performance(
            opponent_roster, team
        )
        targets = [
            team_performance_against_team[0].pokemon,
            team_performance_against_team[1].pokemon,
        ]
        final_team_performance = RosterAnalyzer.calculate_roster_performance(
            roster, targets
        )

        # Add the best complement that isn't already selected
        for performance in final_team_performance:
            if performance.pokemon not in team:
                team.append(performance.pokemon)
                break

        return team

    @staticmethod
    def generate_preset_team() -> List[PvpPokemon]:
        # TODO: Check what this is supposed to do
        raise NotImplementedError

    @staticmethod
    def generate_last_lead_counter(
        roster: List[PvpPokemon],
        opponent_roster: List[PvpPokemon],
        previous_teams: List[List[PvpPokemon]],
    ) -> List[PvpPokemon]:
        """
        Generates a team of Pokemon to counter the opponent's previous lead.

        Args:
            roster (List[PvpPokemon]): The roster of Pokemon.
            opponent_roster (List[PvpPokemon]): The roster of the opponent.
            previous_teams (List[List[PvpPokemon]]): The list of previous teams, with the most recent team first.

        Returns:
            List[PvpPokemon]: The generated team of Pokemon to counter the opponent's previous lead.
        """
        team = []

        # Assuming previousTeams is structured as a list of teams, with the most recent team first
        opponent_previous_lead = previous_teams[0][0]

        # Calculate how the roster performs against the opponent's previous lead
        team_performance = RosterAnalyzer.calculate_roster_performance(
            [opponent_previous_lead], roster
        )

        # Sort scenarios to find the best counter to the opponent's previous lead
        scenarios = sorted(team_performance[0].scenarios, key=lambda x: x.average)

        # Lead with the best counter
        team.append(scenarios[0].opponent)

        # Calculate who counters the lead's counters
        scenarios = RosterAnalyzer.run_bulk_scenarios(
            ScenarioType.NO_BAIT, team[0], opponent_roster
        )
        scenarios = sorted(scenarios, key=lambda x: x.average)

        # Identify the main threats to the lead
        targets = [scenarios[0].opponent, scenarios[1].opponent]

        # Find the best bodyguard for the lead
        team_performance_against_targets = RosterAnalyzer.calculate_roster_performance(
            roster, targets
        )
        for performance in team_performance_against_targets:
            if performance.pokemon not in team:
                team.append(performance.pokemon)
                break

        # Now, round out the team with a Pokémon that complements the first two
        team_performance_against_team = RosterAnalyzer.calculate_roster_performance(
            opponent_roster, team
        )
        targets = [
            performance.pokemon for performance in team_performance_against_team
        ][:2]

        # Find a Pokémon in the roster that performs best against the identified threats
        final_team_performance = RosterAnalyzer.calculate_roster_performance(
            roster, targets
        )
        for performance in final_team_performance:
            if performance.pokemon not in team:
                team.append(performance.pokemon)
                break

        return team

    @staticmethod
    def generate_unbalanced_team(
        roster: List[PvpPokemon], opponent_roster: List[PvpPokemon]
    ) -> List[PvpPokemon]:
        """
        Generates an unbalanced team of Pokémon based on their performance against the opponent's roster.

        Args:
            roster (List[PvpPokemon]): The roster of Pokémon.
            opponent_roster (List[PvpPokemon]): The roster of the opponent's Pokémon.

        Returns:
            List[PvpPokemon]: The unbalanced team of Pokémon.

        """
        team = []

        # Calculate the performance of the roster against the opponent's roster
        team_performance = RosterAnalyzer.calculate_roster_performance(
            roster, opponent_roster
        )

        # Choose the best two average Pokémon based on their overall performance
        team.extend([team_performance[0].pokemon, team_performance[1].pokemon])

        # Analyze how the opponent's roster performs against the selected team
        # to identify which opponents are the biggest threats
        team_performance_against_team = RosterAnalyzer.calculate_roster_performance(
            opponent_roster, team[:2]
        )
        targets = [
            team_performance_against_team[0].pokemon,
            team_performance_against_team[1].pokemon,
        ]

        # Now find the best counter (bodyguard) in the roster against those threats
        team_performance = RosterAnalyzer.calculate_roster_performance(roster, targets)

        # Add the best counter that isn't already in the team as the lead
        for performance in team_performance:
            if performance.pokemon not in team:
                team.insert(
                    0, performance.pokemon
                )  # Insert this Pokémon at the beginning of the team as the lead
                break

        return team

    @staticmethod
    def generate_counter_team(
        roster: List[PvpPokemon], opponent_roster: List[PvpPokemon]
    ) -> List[PvpPokemon]:
        """
        Generates a list of Pokémon that form a counter team against the opponent's roster.

        Args:
            roster (List[PvpPokemon]): The player's roster of Pokémon.
            opponent_roster (List[PvpPokemon]): The opponent's roster of Pokémon.

        Returns:
            List[PvpPokemon]: A list of Pokémon that form a counter team against the opponent's roster.
        """
        team = []

        # Calculate how well each Pokémon in the roster performs against the opponent's roster
        team_performance = RosterAnalyzer.calculate_roster_performance(
            opponent_roster, roster
        )
        top_performance = team_performance[0]

        # Sort the scenarios to find the best counter to the opponent's best Pokémon
        scenarios = sorted(top_performance.scenarios, key=lambda x: x.average)

        # Lead with the best counter to the opponent's most effective Pokémon
        team.append(scenarios[0].opponent)

        # Run scenarios to see who counters the lead's counters from the opponent roster
        scenarios = RosterAnalyzer.run_bulk_scenarios(
            ScenarioType.NO_BAIT, team[0], opponent_roster
        )
        scenarios = sorted(scenarios, key=lambda x: x.average)

        # Identify the primary threats to the lead
        targets = [scenarios[0].opponent, scenarios[1].opponent]

        # Calculate which of the Pokémon best counters those threats
        team_performance_against_targets = RosterAnalyzer.calculate_roster_performance(
            roster, targets
        )

        # Add the best bodyguard (counter to threats) that isn't already selected
        for performance in team_performance_against_targets:
            if performance.pokemon not in team:
                team.append(performance.pokemon)
                break

        # Now, identify a third Pokémon to round out the team, focusing on countering collective counters
        team_performance_against_team = RosterAnalyzer.calculate_roster_performance(
            opponent_roster, team
        )
        targets = [
            team_performance_against_team[0].pokemon,
            team_performance_against_team[1].pokemon,
        ]

        final_team_performance = RosterAnalyzer.calculate_roster_performance(
            roster, targets
        )

        # Add another counter that isn't already selected, complementing the first two
        for performance in final_team_performance:
            if performance.pokemon not in team:
                team.append(performance.pokemon)
                break

        return team
