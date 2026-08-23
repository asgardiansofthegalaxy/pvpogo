import math
import random
from typing import List, Optional

from pypogo.action import PvpAction
from pypogo.ai.interface import AInterface, AIStatus
from pypogo.ai.pvpoke.roster_analysis import RosterAnalyzer
from pypogo.ai.pvpoke.team_generation import TeamGenerator
from pypogo.constants import BattlePhase
from pypogo.moves import MoveKind, PvpMove
from pypogo.player import Player
from pypogo.pokemon import PvpPokemon

from .constants import (
    AILevel,
    AI_ARCHETYPES,
    DecisionOption,
    DecisionType,
    ScenarioType,
    Strategy,
    SWITCH_STRATEGIES,
)
from .utils import choose_option


# Order used whenever a heuristic produces nothing legal. Mirrors NaiveAI so a
# PvPokeAI always has a legal move to fall back on and never stalls a battle.
FALLBACK_ACTIONS = (
    PvpAction.CHARGED1,
    PvpAction.CHARGED2,
    PvpAction.SHIELD,
    PvpAction.FAST,
    PvpAction.WAIT,
    PvpAction.SWITCH1,
    PvpAction.SWITCH2,
)


class PvPokeAI(AInterface):
    def __init__(
        self,
        player: Player,
        level: AILevel = AILevel.NOVICE,
        name: str = "PvPokeAI",
    ):
        self.player = player
        self.name = name
        self.level = level
        self.archetype = AI_ARCHETYPES[self.level]
        self.previous_strategy = None
        self.current_strategy = Strategy.DEFAULT
        self.last_turn_evaluated = 0
        self.party_size = 3
        # run_scenario costs nine simulated battles, and the shield/switch
        # heuristics ask for the same matchup repeatedly within one battle.
        self._scenario_cache = {}

    def select_team(
        self,
        previous_teams: Optional[List[List[PvpPokemon]]] = None,
        previous_result: str = None,
        selection_strategy: DecisionType = None,
    ) -> List[PvpPokemon]:
        """
        Selects a team of Pokemon for battle based on the current opponent,
        previous teams, and the previous result.

        Args:
            previous_teams (List[List[PvpPokemon]], optional): Teams used in
                earlier rounds, most recent last.
            previous_result (str, optional): The result of the previous battle.
                Can be "win", "loss", or None.
            selection_strategy (DecisionType, optional): Force a strategy
                instead of picking one by weight.

        Returns:
            List[PvpPokemon]: The team of Pokemon selected for battle.
        """
        opponent = self.opponent
        if opponent is None:
            return []

        previous_teams = previous_teams or []
        team = []
        player_roster = self.player.roster
        opponent_roster = opponent.roster

        if selection_strategy is None:
            selection_strategy = self._get_team_selection_strategy(
                opponent_roster, previous_result
            )

        # Strategies that need a previous team fall back to a fresh pick when
        # this is the opening round.
        if not previous_teams and selection_strategy in (
            DecisionType.SAME_TEAM,
            DecisionType.SAME_TEAM_DIFFERENT_LEAD,
            DecisionType.COUNTER_LAST_LEAD,
        ):
            selection_strategy = DecisionType.BEST

        # Generate a basic team based on random selection
        if selection_strategy == DecisionType.BASIC:
            team = random.sample(player_roster, min(self.party_size, len(player_roster)))

        # Generate the best team available
        elif selection_strategy == DecisionType.BEST:
            team = TeamGenerator.generate_best_team(player_roster, opponent_roster)

        # Generate a team that counters the opponent's team
        elif selection_strategy == DecisionType.COUNTER:
            team = TeamGenerator.generate_counter_team(player_roster, opponent_roster)

        # Generate an unbalanced team e.g two steel types and a bulky water type
        elif selection_strategy == DecisionType.UNBALANCED:
            team = TeamGenerator.generate_unbalanced_team(
                player_roster, opponent_roster
            )

        # Generate a team with the same Pokemon as the previous round, but with a different lead
        elif selection_strategy == DecisionType.SAME_TEAM_DIFFERENT_LEAD:
            previous_team = previous_teams[-1]
            if len(previous_team) >= 2:
                team = [previous_team[1], previous_team[0], *previous_team[2:]]
            else:
                team = list(previous_team)

        # Generate a team that counters the opponent's last lead
        elif selection_strategy == DecisionType.COUNTER_LAST_LEAD:
            team = TeamGenerator.generate_last_lead_counter(
                player_roster, opponent_roster, previous_teams
            )

        # Use a preset team
        elif selection_strategy == DecisionType.PRESET:
            team = TeamGenerator.generate_preset_team()

        # Use the same team as the previous round
        elif selection_strategy == DecisionType.SAME_TEAM:
            team = previous_teams[-1]

        return team

    def decide_action(self, battle_phase: BattlePhase):
        """
        Determines the action to be taken by the AI player in a PvP battle.

        Args:
            battle_phase (BattlePhase): The current phase of the battle.

        Returns:
            tuple[AIStatus, PvpAction]: The status of the decision and the
            action to take.
        """
        opponent = self.opponent
        if opponent is None:
            return AIStatus.AI_ERROR_BAD_VALUE, PvpAction.ACT_NULL

        if battle_phase == BattlePhase.GAME_OVER:
            return AIStatus.AI_ERROR_FAIL, PvpAction.ACT_NULL

        # The opponent launched a charged move and we get to answer it.
        if battle_phase == BattlePhase.SUSPEND_CHARGED:
            action = PvpAction.SHIELD if self.decide_shield() else PvpAction.WAIT
            return self._resolve(action, battle_phase)

        # Our active Pokemon fainted, so the only thing to do is bring in the
        # next one.
        if not self.player.is_active_alive:
            return self._resolve(self._switch_action(), battle_phase)

        return self._resolve(self._decide_battle_action(battle_phase), battle_phase)

    def _decide_battle_action(self, battle_phase: BattlePhase) -> Optional[PvpAction]:
        """
        The core turn-by-turn heuristic: farm energy, overfarm, or switch out.

        Returns:
            PvpAction | None: The action the heuristics picked, or None to let
            the baseline attack logic decide.
        """
        opponent = self.opponent
        action = None
        attacker = self.player.active_pokemon
        defender = opponent.active_pokemon

        # NOTE: nothing selects a non-DEFAULT strategy yet, so the switch and
        # overfarm branches below stay dormant in normal play. Implementing the
        # strategy state machine (what makes an archetype pick SWITCH_FARM or
        # FARM_ENERGY, and when) is the next piece of work on this AI; see
        # _process_strategy. A naive "re-evaluate every turn" version was tried
        # and made CHAMPION play worse than NOVICE by thrashing between
        # strategies, so it needs a real reaction-time/hysteresis model.

        # Calculate how many fast moves the opponent can get off before
        # our next fast move
        extra_fast_moves = math.floor(
            (attacker.fast_move.cooldown_turns - defender.cooldown_turns)
            / defender.fast_move.cooldown_turns
        )

        # Give some extra room for overfarming
        if not self._is_switching():
            extra_fast_moves += 1

        if 0 < defender.cooldown_turns < attacker.fast_move.cooldown_turns:
            extra_fast_moves = max(extra_fast_moves, 1)

        future_energy = defender.energy + (
            extra_fast_moves * defender.fast_move.energy_gain
        )
        future_damage = defender.calculate_potential_damage(
            opponent=attacker, stored_energy=future_energy
        )

        if (
            future_damage >= attacker.hp
            and self.current_strategy == Strategy.FARM_ENERGY
        ):
            self._process_strategy(Strategy.DEFAULT)

        if self._is_switching() and self.player.switch_timer == 0:
            perform_switch = False

            if self.current_strategy == Strategy.SWITCH_BASIC and (
                self.turn - self.last_turn_evaluated >= self.archetype.reaction_time
            ):
                perform_switch = True

            if self.current_strategy == Strategy.SWITCH_FARM:
                if (
                    future_damage >= attacker.hp
                    or future_damage >= attacker.full_hp * 0.14
                ):
                    perform_switch = True

                if attacker.hp / attacker.full_hp < 0.2:
                    perform_switch = True

            if perform_switch:
                self.last_turn_evaluated = self.turn
                action = self._switch_action()

        # Potentially farm more energy than needed
        if (
            self._has_strategy(Strategy.OVERFARM)
            and not self._is_switching()
            and opponent.get_remaining_pokemon() > 1
        ):
            overfarm_chance = 2
            overfarm_chance += round((50 - defender.energy) / 10)

            if future_damage >= attacker.hp or future_damage >= attacker.full_hp * 0.15:
                overfarm_chance = -1

            if attacker.energy == 100:
                overfarm_chance = -1

            # Don't overfarm with Power-Up Punch or Acid Spray
            for move in attacker.charged_moves:
                if move.name in ["Power-Up Punch", "Acid Spray"]:
                    overfarm_chance = -1

            # Don't overfarm if this Pokemon has extremely low HP
            if attacker.hp / attacker.full_hp < 0.2:
                overfarm_chance = -1

            # Perform overfarm
            if overfarm_chance > 0 and math.floor(random.random() * overfarm_chance) > 0:
                action = PvpAction.FAST

        if action is None:
            action = self._baseline_action(battle_phase)

        return action

    def _baseline_action(self, battle_phase: BattlePhase) -> Optional[PvpAction]:
        """
        Default attacking behaviour when no strategy fired: throw the hardest
        affordable charged move, otherwise keep building energy with a fast move.
        """
        attacker = self.player.active_pokemon
        defender = self.opponent.active_pokemon

        affordable = [
            action
            for action in (PvpAction.CHARGED1, PvpAction.CHARGED2)
            if self.is_valid_action(action, battle_phase)
        ]
        if affordable:
            return max(
                affordable,
                key=lambda a: attacker.calculate_damage(a.move_kind, defender),
            )

        for action in (PvpAction.FAST, PvpAction.WAIT):
            if self.is_valid_action(action, battle_phase):
                return action

        return None

    def _resolve(self, action: Optional[PvpAction], battle_phase: BattlePhase):
        """
        Validate a chosen action, falling back to the first legal alternative.

        Returns:
            tuple[AIStatus, PvpAction]
        """
        if action is not None and self.is_valid_action(action, battle_phase):
            return AIStatus.AI_SUCCESS, action

        for fallback in FALLBACK_ACTIONS:
            if self.is_valid_action(fallback, battle_phase):
                return AIStatus.AI_SUCCESS, fallback

        return AIStatus.AI_ERROR_FAIL, PvpAction.ACT_NULL

    def _switch_action(self) -> Optional[PvpAction]:
        """
        Translate the switch target chosen by `decide_switch` into the
        SWITCH1/SWITCH2 action the battle understands.

        `Player.do_switch` counts through the team skipping the active and any
        fainted Pokemon, so SWITCH1 is the first such Pokemon and SWITCH2 the
        second.
        """
        target_idx = self.decide_switch()
        if target_idx is None:
            return None

        available = [
            i
            for i, pokemon in enumerate(self.player.team)
            if pokemon.hp > 0 and i != self.player._active_pokemon_idx
        ]
        if target_idx not in available:
            return None

        return PvpAction.SWITCH1 if available.index(target_idx) == 0 else PvpAction.SWITCH2

    def decide_switch(self) -> Optional[int]:
        """
        Determines which Pokemon to switch to based on the current battle scenario.

        Returns:
            int | None: The index of the Pokemon to switch to, or None if there
            is nothing to switch to.
        """
        opponent = self.opponent
        if opponent is None:
            return None

        switch_options = []
        team = self.player.team
        attacker = self.player.active_pokemon
        defender = opponent.active_pokemon

        for i, pokemon in enumerate(team):
            if pokemon.hp > 0 and pokemon is not attacker:
                scenario = self._run_scenario(ScenarioType.NO_BAIT, pokemon, defender)
                weight = 1

                # Adjust the weight based on the scenario's outcome
                if scenario.average < 500:
                    weight = round(math.pow(scenario.average / 100, 4) / 20)
                else:
                    if opponent.switch_timer > 10 or attacker.hp <= 0:
                        # Favor hard counter if the opponent is switch locked or if the active Pokémon has fainted
                        weight = round(math.pow((scenario.average - 250) / 100, 4))
                    else:
                        # Favor softer counter otherwise
                        weight = round(math.pow((1000 - scenario.average) / 100, 4))

                if weight < 1:
                    weight = 1

                switch_options.append(DecisionOption(i, weight))

        if not switch_options:
            return None

        # If the AI has the BAD_DECISION_PROTECTION strategy, it will only consider the best switch
        if self._has_strategy(Strategy.BAD_DECISION_PROTECTION):
            # Sort options by weight in descending order
            switch_options.sort(key=lambda x: x.weight, reverse=True)
            # If the first option significantly outweighs the next, discard the rest
            if (
                len(switch_options) > 1
                and switch_options[0].weight > switch_options[1].weight * 4
            ):
                switch_options = switch_options[:1]

        switch_idx = choose_option(switch_options).value
        return switch_idx

    def decide_shield(self) -> bool:
        """
        Determines whether the player should use a shield or not in the current battle scenario.

        Returns:
            bool: True if the player should use a shield, False otherwise.
        """
        opponent = self.opponent
        if opponent is None:
            return False

        defender = self.player.active_pokemon
        attacker = opponent.active_pokemon

        if not attacker.charged_moves:
            return False

        # First, how hot are we looking in this current matchup? Rate our own
        # Pokemon against theirs.
        scenario = self._run_scenario(ScenarioType.NO_BAIT, defender, attacker)

        # Next, guess the opponent's move

        # The opponent's fastest charged move (in terms of energy) is the minimum energy required
        min_energy = min(attacker.charged_moves, key=lambda x: x.energy).energy

        # Estimate the opponent's amount of energy by looking at our
        # attacker's energy and adding a random amount and comparing it
        # to the minimum energy the opponent needs to launch an attack
        energy_guess_range = self.archetype.energy_guess_range
        estimated_energy = max(
            min_energy,
            attacker.energy + (random.randint(-energy_guess_range, energy_guess_range)),
        )

        # The opponent's charged moves that can be used with the estimated energy
        possible_moves = []
        for move in attacker.charged_moves:
            if estimated_energy >= move.energy:
                possible_moves.append(PvpMove(move, attacker, defender))
        possible_moves.sort(key=lambda x: x.damage, reverse=True)

        if not possible_moves:
            return False

        # Now that we have the possible moves, let's guess which one the opponent will use
        options = []
        for i, move in enumerate(possible_moves):
            move_weight = 1

            # Is the opponent low on HP? They're using the higher damage move
            if i == 0 and attacker.hp / attacker.full_hp <= 0.25:
                move_weight += 8

                # TODO: Double check why Acid Spray is weighted differently
                if move.name == "Acid Spray":
                    move_weight += 12

            # Be more cautious when we have more shields
            if i == 0:
                move_weight += self.player.shields

            # If we're down to our last Pokemon, weigh the higher damage move more heavily
            if self.player.get_remaining_pokemon() == 1 and move.damage >= defender.hp:
                move_weight += 4

            # Is this move with low damage and high energy? Then the opponent is probably not using it
            if (
                i == 1
                and move.damage < possible_moves[0].damage
                and move.energy >= possible_moves[0].energy
                and move.name != "Acid Spray"
            ):
                options[0].weight += 20
            options.append(DecisionOption(i, move_weight))

        guessed_move = possible_moves[choose_option(options).value]

        # We've guessed the move, now let's analyze if we should shield like a player would
        yes_weight = 4 + ((3 - self.level.value) * 2)
        no_weight = 4 + ((3 - self.level.value) * 2)

        # Will this attack do a lot of damage? Weight the decision accordingly
        move_damage = guessed_move.damage
        damage_weight = min(
            round((move_damage / max(defender.hp, defender.full_hp / 2)) * 10),
            10,
        )

        # Give more weight to shielding high damage moves over low damage moves
        if damage_weight >= 5:
            yes_weight += (damage_weight - 3) * (self.player.shields + 1)
        else:
            no_weight += (8 - damage_weight) * 2

        # Prefer to shield hard hitting/knockout moves in good matchups over bad matchups
        fast_move_damage = attacker.calculate_damage(MoveKind.FAST, defender)
        if damage_weight >= 6 or move_damage + (fast_move_damage * 2) >= defender.hp:
            if self.player.get_remaining_pokemon() > 1:
                yes_rating = scenario.rating - 400
                no_rating = 400 - scenario.rating

                if defender.hp / defender.full_hp < 0.35:
                    yes_rating = scenario.rating - 500
                    no_rating = 500 - scenario.rating

                # If we can't switch, prefer to shield good matchups and let bad matchups go
                if (
                    self.player.switch_timer > 0
                    and self.player.get_remaining_pokemon() > 1
                ):
                    yes_rating *= 2
                    no_rating *= 2
                yes_weight += round((yes_rating / 100) * damage_weight)
                no_weight += round((no_rating / 100) * (10 - damage_weight))
            else:
                yes_weight += damage_weight
                no_weight -= damage_weight

        # If the opponent has been using shields, consider shielding more if we don't do advanced shielding
        if (
            opponent.shields_used > 0
            and damage_weight > 2
            and not self._has_strategy(Strategy.ADVANCED_SHIELDING)
        ):
            yes_weight += 4

        # Is our Pokemon close to a move that will faint or seriously injure the attacker?
        # If so, consider shielding
        for move in defender.charged_moves:
            turns_away = (
                (move.energy - defender.energy) / defender.fast_move.energy_gain
            ) * (defender.fast_move.cooldown_turns)
            if (
                move_damage >= attacker.hp
                or (move_damage >= defender.full_hp * 0.8)
                and turns_away <= 1
            ):
                if self._has_strategy(Strategy.ADVANCED_SHIELDING):
                    yes_weight += 4

        # Do we have shield advantage? Then let's try to preserve it
        if (
            self.player.get_remaining_pokemon() > 1
            and opponent.starting_shields >= self.player.starting_shields
            and self.player.shields_used > 0
        ):
            yes_weight = round(yes_weight / 2)
            if scenario.rating < 500:
                yes_weight = round(yes_weight / 4)

        # If we're down to our last Pokemon, better shield
        if self.player.get_remaining_pokemon() == 1:
            yes_weight *= 2
            no_weight = round(no_weight / 4)

        # If one of these options is significantly more weighted than the other, make it the only option
        if self._has_strategy(Strategy.BAD_DECISION_PROTECTION):
            if no_weight > 0 and yes_weight / no_weight >= 4:
                no_weight = 0
            elif yes_weight > 0 and no_weight / yes_weight >= 4:
                yes_weight = 0

        # choose_option builds a bucket from the weights, so negatives would
        # silently drop an option rather than de-prioritise it.
        yes_weight = max(yes_weight, 0)
        no_weight = max(no_weight, 0)
        if yes_weight == 0 and no_weight == 0:
            return False

        options = [
            DecisionOption(True, yes_weight),
            DecisionOption(False, no_weight),
        ]

        will_shield = choose_option(options).value

        return will_shield

    def _run_scenario(
        self, scenario_type: ScenarioType, attacker: PvpPokemon, defender: PvpPokemon
    ):
        """
        Memoised `RosterAnalyzer.run_scenario`.

        Each call simulates nine battles, and the shield/switch heuristics ask
        about the same pair of Pokemon many times inside a single battle.
        """
        key = (scenario_type, self._matchup_key(attacker), self._matchup_key(defender))
        if key not in self._scenario_cache:
            self._scenario_cache[key] = RosterAnalyzer.run_scenario(
                scenario_type, attacker, defender
            )
        return self._scenario_cache[key]

    @staticmethod
    def _matchup_key(pokemon: PvpPokemon):
        """A hashable identity for a Pokemon's matchup-relevant configuration."""
        return (
            pokemon.pdex_mon.species_id,
            pokemon.level,
            pokemon.ivs.attack,
            pokemon.ivs.defense,
            pokemon.ivs.stamina,
            pokemon.fast_move.move_id,
            tuple(move.move_id for move in pokemon.charged_moves),
        )

    def _is_switching(self) -> bool:
        """
        Whether the current strategy is one of the switch strategies.

        Strategy is a Flag, so this has to be a bitwise test -- the old
        `"SWITCH" in self.current_strategy.value` check raised TypeError
        because `.value` is an int.
        """
        return bool(self.current_strategy & SWITCH_STRATEGIES)

    def _has_strategy(self, strategy: Strategy) -> bool:
        """Check if the AI has a specific strategy.

        Args:
            strategy (Strategy): The strategy to check.

        Returns:
            bool: True if the AI has the specified strategy, False otherwise.
        """
        return strategy in self.archetype.strategies

    def _get_team_selection_strategy(
        self, opponent_roster: List[PvpPokemon], previous_result: str
    ) -> DecisionType:
        """
        Generate a selection strategy based on the previous battle result.

        Args:
            opponent_roster (List[PvpPokemon]): The opponent's roster.
            previous_result (str): The result of the previous battle.

        Returns:
            DecisionType: The selection strategy to be used.
        """
        # In Single 3v3 mode, use the Basic option most of the time depending on difficulty
        basic_weight = 1
        if len(opponent_roster) < 6:
            basic_weight = 4 * (4 - self.level.value)

            # Make the teams more random in GO Battle League
            if self.party_size == 3:  # TODO need to check for cup type
                basic_weight *= 3

        # Team selection strategies
        selection_strategies = []
        if not previous_result:
            # If this is a fresh round, use these strategies
            selection_strategies.extend(
                [
                    DecisionOption(DecisionType.BASIC, basic_weight),
                    DecisionOption(DecisionType.BEST, 6),
                    DecisionOption(DecisionType.COUNTER, 6),
                    DecisionOption(DecisionType.UNBALANCED, 3),
                ]
            )
        else:
            # If this is subsequent round, use these strategies
            win_weight = 12 if previous_result == "loss" else 3
            lose_weight = 12 if previous_result == "win" else 3
            selection_strategies.extend(
                [
                    DecisionOption(DecisionType.SAME_TEAM, win_weight),
                    DecisionOption(DecisionType.SAME_TEAM_DIFFERENT_LEAD, win_weight),
                    DecisionOption(DecisionType.COUNTER_LAST_LEAD, lose_weight),
                    DecisionOption(DecisionType.COUNTER, lose_weight),
                ]
            )

        # TODO: support DecisionType.PRESET

        return choose_option(selection_strategies).value

    def _process_strategy(self, strategy: Strategy):
        """
        Process the given strategy and update player attributes accordingly.

        Args:
            strategy (Strategy): The strategy to be processed.
        """
        self.previous_strategy = self.current_strategy
        self.current_strategy = strategy
