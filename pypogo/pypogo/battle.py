import random
import time
from typing import Optional

from pypogo.pokemon import PvpPokemon

from .action import PvpAction
from .constants import (
    SWITCH_TIMEOUT_TURNS,
    SWITCH_TURNS,
    BattlePhase,
    CMPRule,
)
from .player import Player


class PvpBattle:
    def __init__(
        self, player_one: Player, player_two: Player, keep_history: bool = True
    ):
        self.p1 = player_one
        self.p2 = player_two
        self.p1_action: PvpAction = PvpAction.ACT_NULL
        self.p2_action: PvpAction = PvpAction.ACT_NULL
        self._turn: int = 0
        self._phase: BattlePhase = BattlePhase.COUNTDOWN
        self.cmp_rule: CMPRule = CMPRule.CMP_IDEAL
        self.cmp_alt_state: bool = False
        self._history: Optional[list] = [] if keep_history else None
        self._keep_history = keep_history

        # Give each player a handle on its opponent and on this battle, so an
        # AI can read battle context (opponent's active Pokemon, current turn)
        # without every decide_* call having to thread it through.
        self.p1.enter_battle(self, opponent=self.p2)
        self.p2.enter_battle(self, opponent=self.p1)

    @property
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, value):
        self._phase = BattlePhase(value)
        if self._keep_history:
            self.record_history()

    @property
    def turn(self):
        return self._turn

    @turn.setter
    def turn(self, value):
        self._turn = value
        if self._keep_history:
            self.record_history()

    def record_history(self):
        """
        Records the current state of the battle.
        """
        move_p1 = ""
        move_p2 = ""

        if self.p1_action.is_fast:
            move_p1 = self.p1.active_pokemon.fast_move.name
        elif self.p1_action.is_charged:
            move_p1 = self.p1.active_pokemon.get_move(self.p1_action.move_kind).name
        if self.p2_action.is_fast:
            move_p2 = self.p2.active_pokemon.fast_move.name
        elif self.p2_action.is_charged:
            move_p2 = self.p2.active_pokemon.get_move(self.p2_action.move_kind).name

        self._history.append(
            {
                "Turn": self.turn,
                "Phase": self.phase.name,
                "Player1": {
                    "Pokemon": self.p1.active_pokemon.pdex_mon.species_name,
                    "HP": self.p1.active_pokemon.hp,
                    "Energy": self.p1.active_pokemon.energy,
                    "Action": self.p1_action.name,
                    "Switch Timer": self.p1.switch_timer,
                    "Move": move_p1,
                },
                "Player2": {
                    "Pokemon": self.p2.active_pokemon.pdex_mon.species_name,
                    "HP": self.p2.active_pokemon.hp,
                    "Energy": self.p2.active_pokemon.energy,
                    "Action": self.p2_action.name,
                    "Switch Timer": self.p2.switch_timer,
                    "Move": move_p2,
                },
            }
        )

    def simulate(self) -> int:
        """
        Simulates a battle between two players.

        Returns:
            int: The number of turns taken in the battle.
        """
        assert self.phase == BattlePhase.COUNTDOWN

        # Give opportunity to swap during countdown
        self.p1_action = self.p1.decide_action(self.phase)
        self.p2_action = self.p2.decide_action(self.phase)

        self.phase = BattlePhase.NEUTRAL

        while not self._eval_turn():
            # Decrement turn counter, switch timer, and cooldowns
            self.p1.decrease_switch_timer(1)
            self.p2.decrease_switch_timer(1)
            self.p1.decrease_cooldown()
            self.p2.decrease_cooldown()
            self.turn += 1

            self.p1_action = PvpAction.ACT_NULL
            self.p2_action = PvpAction.ACT_NULL
            self.p1_action = self.p1.decide_action(self.phase)
            self.p2_action = self.p2.decide_action(self.phase)

            # Check for fainted pokemon
            self._handle_faints()

        self.phase = BattlePhase.GAME_OVER

        return self.turn

    def is_battle_over(self) -> bool:
        """
        Check if the battle is over.

        Returns:
            bool: True if the battle is over, False otherwise.
        """
        return (
            self.phase == BattlePhase.GAME_OVER
            or self.p1.get_remaining_pokemon() <= 0
            or self.p2.get_remaining_pokemon() <= 0
        )

    def is_player_one_winner(self) -> bool:
        """
        Determines if player one is the winner of the battle.

        Returns:
            bool: True if player one is the winner, False otherwise.
        """
        assert self.is_battle_over()
        return (
            self.p2.get_remaining_pokemon() <= 0 and self.p1.get_remaining_pokemon() > 0
        )

    def get_battle_winner(self):
        """
        Determines the winner of the battle.

        Returns:
            Player: The winning player object, or None if it's a tie.
        """
        # Detect a tie
        if (
            self.p1.get_remaining_pokemon() == 0
            and self.p2.get_remaining_pokemon() == 0
        ):
            return None
        return self.p1 if self.is_player_one_winner() else self.p2

    def get_history(self):
        """
        Returns the battle history.

        Returns:
            dict: A dictionary containing the battle history.
        """
        return self._history

    def _eval_turn(self) -> bool:
        """
        Evaluate the turn of the battle.

        This method checks if both players have chosen valid actions and then evaluates the turn
        based on the current battle mode. Currently, only 'SIMULATE' battle mode is supported.

        Returns:
            bool: True if the turn was successfully evaluated, False otherwise.
        """
        assert self.p1_action != PvpAction.ACT_NULL
        assert self.p2_action != PvpAction.ACT_NULL

        assert self.p1.ai.is_valid_action(self.p1_action, self.phase)
        assert self.p2.ai.is_valid_action(
            self.p2_action, self.phase
        ), f"{self.p2_action} is not valid in {self.phase}"

        # Currently only 'SIMULATE' battle mode is supported.
        return self._eval_turn_simulated()

    def _eval_turn_simulated(self) -> bool:
        """
        Evaluate the simulated turn in the battle.

        This method evaluates the actions taken by both players in the battle and processes them accordingly.
        It checks the battle phase and performs the necessary actions based on the phase.
        If both players choose to wait, the evaluation is skipped.

        Returns:
            True if the battle is over, False otherwise.
        """
        assert self.phase != BattlePhase.COUNTDOWN
        assert self.phase != BattlePhase.SUSPEND_CHARGED_ATTACK
        assert self.phase != BattlePhase.SUSPEND_CHARGED_SHIELD
        assert self.phase != BattlePhase.SUSPEND_CHARGED_NO_SHIELD
        assert self.phase != BattlePhase.SUSPEND_SWITCH_P1
        assert self.phase != BattlePhase.SUSPEND_SWITCH_P2
        assert self.phase != BattlePhase.GAME_OVER
        assert self.phase != BattlePhase.SUSPEND_CHARGED

        # Force Pokemon with cooldowns to wait
        if (
            self.p1_action != PvpAction.WAIT
            and self.p1.has_cooldown
            and not (self.p1_action.is_switch and self.p1.can_switch)
        ):
            self.p1_action = PvpAction.WAIT
        if (
            self.p2_action != PvpAction.WAIT
            and self.p2.has_cooldown
            and not (self.p2_action.is_switch and self.p2.can_switch)
        ):
            self.p2_action = PvpAction.WAIT

        # Skip evaluation if both players waited
        if self.p1_action == PvpAction.WAIT and self.p2_action == PvpAction.WAIT:
            return False

        # Process actions in the NEUTRAL phase
        if self.phase == BattlePhase.NEUTRAL:
            self._process_neutral_phase_actions(self.p1_action, self.p2_action)

        # Process actions in the SUSPEND_SWITCH_TIE phase
        elif self.phase == BattlePhase.SUSPEND_SWITCH_TIE:
            self._process_suspend_switch_tie_phase_actions(
                self.p1_action, self.p2_action
            )

        return self.is_battle_over()

    def _process_neutral_phase_actions(self, a1: PvpAction, a2: PvpAction):
        """
        Process the neutral phase actions during a battle.

        Args:
            a1 (PvpAction): The action chosen by player one.
            a2 (PvpAction): The action chosen by player two.
        """
        # Handle Switches first (not resulting from faints)
        if a1.is_switch:
            assert self.p1.can_switch
            self.p1.do_switch(self.p1_action == PvpAction.SWITCH1)
            self.p1.start_switch_timer(SWITCH_TURNS)

        if a2.is_switch:
            assert self.p2.can_switch
            self.p2.do_switch(self.p2_action == PvpAction.SWITCH1)
            self.p2.start_switch_timer(SWITCH_TURNS)

        # Do fast attacks (always go before charged attacks)
        if a1.is_fast:
            self.p1.do_fast(defender=self.p2)
        if a2.is_fast:
            self.p2.do_fast(defender=self.p1)

        # Handle charged moves
        if a1.is_charged and a2.is_charged:
            # Determine CMP winner and execute charged moves
            if self._is_p1_cmp_winner():
                self._do_charged(attacker=self.p1, defender=self.p2, action=a1)
                if self.p2.is_active_alive:
                    self._do_charged(attacker=self.p2, defender=self.p1, action=a2)
            else:
                self._do_charged(attacker=self.p2, defender=self.p1, action=a2)
                if self.p1.is_active_alive:
                    self._do_charged(attacker=self.p1, defender=self.p2, action=a1)
        elif a1.is_charged:
            self._do_charged(attacker=self.p1, defender=self.p2, action=a1)
        elif a2.is_charged:
            self._do_charged(attacker=self.p2, defender=self.p1, action=a2)

    def _process_suspend_switch_tie_phase_actions(self, a1: PvpAction, a2: PvpAction):
        """
        Process switch actions during the SUSPEND_SWITCH_TIE phase.

        Args:
            a1 (PvpAction): The action performed by player one.
            a2 (PvpAction): The action performed by player two.
        """
        if a1.is_switch:
            self.p1.do_switch(self.p1_action == PvpAction.SWITCH1)
        if a2.is_switch:
            self.p2.do_switch(self.p2_action == PvpAction.SWITCH1)

    def _do_charged(self, attacker: Player, defender: Player, action: PvpAction):
        """
        Executes a charged move during a battle.

        Args:
            attacker (Player): The player who is executing the move.
            defender (Player): The player who is defending against the move.
            action (PvpAction): The action representing the charged move.
        """
        move_kind = action.move_kind

        move = attacker.active_pokemon.get_move(move_kind)
        assert move.energy <= attacker.active_pokemon.energy
        attacker.decrease_energy(move.energy)

        if defender._shields > 0:
            self.phase = BattlePhase.SUSPEND_CHARGED
            reaction = defender.decide_action(self.phase)
            self.phase = BattlePhase.NEUTRAL
            if reaction == PvpAction.SHIELD:
                defender.use_shield()
                # TODO: Calculate that tiny bit of damage that leaks
                return

        damage = attacker.active_pokemon.calculate_damage(
            move_kind, defender.active_pokemon
        )
        defender.active_pokemon.hp = max(defender.active_pokemon.hp - damage, 0)

    def _is_p1_cmp_winner(self) -> bool:  # TODO Rename method
        """
        Determines if player one is the winner based on the comparison rule.

        Returns:
            bool: True if player one is the winner, False otherwise.

        Raises:
            ValueError: If an unknown comparison rule is encountered.
        """
        a1 = self.p2.active_pokemon.attack
        a2 = self.p1.active_pokemon.attack

        if self.cmp_rule == CMPRule.CMP_IDEAL:
            if a1 == a2:
                random.seed(time.time())
                return random.choice([True, False])
            else:
                return a2 < a1

        elif self.cmp_rule == CMPRule.CMP_ALTERNATE:
            self.cmp_alt_state = not self.cmp_alt_state
            return not self.cmp_alt_state

        elif self.cmp_rule == CMPRule.CMP_FAVOR_P1:
            return True

        elif self.cmp_rule == CMPRule.CMP_FAVOR_P2:
            return False

        else:
            # Handle unknown CMP rule case
            raise ValueError("Encountered unknown CMP Rule!")

    def _handle_faints(self):
        """
        Handles the logic when one or both Pokemon faint during a battle.

        If both Pokemon faint, the battle enters the SUSPEND_SWITCH_TIE phase and the players' actions are decided
        until the switch timeout is reached or one of the players decides to switch their Pokemon.

        If only one Pokemon faints, the battle continues until the switch timeout is reached or the remaining Pokemon
        decides to switch.

        Raises:
            AssertionError: If the active Pokemon of either player is not alive after handling faints.
        """
        # Check if the battle is over first
        if self.is_battle_over():
            return

        # Both fainted. Wait for swap
        if not (self.p1.is_active_alive or self.p2.is_active_alive):
            self.phase = BattlePhase.SUSPEND_SWITCH_TIE
            self.p1_action = self.p1.decide_action(self.phase)
            self.p2_action = self.p2.decide_action(self.phase)

            # Wait for both players to pick
            swap_timeout = SWITCH_TIMEOUT_TURNS
            while swap_timeout > 0 and (
                self.p1_action == PvpAction.WAIT or self.p2_action == PvpAction.WAIT
            ):
                self._eval_turn()
                self.turn += 1
                self.p1.decrease_switch_timer(1)
                self.p2.decrease_switch_timer(1)

                self.p1_action = PvpAction.ACT_NULL
                self.p2_action = PvpAction.ACT_NULL
                self.p1.decide_action(self.phase)
                self.p2.decide_action(self.phase)
                swap_timeout -= 1

            # Force swap if they ran out the clock
            if not self.p1.is_active_alive and self.p1_action == PvpAction.WAIT:
                self.p1_action = PvpAction.SWITCH1
            if not self.p2.is_active_alive and self.p2_action == PvpAction.WAIT:
                self.p2_action = PvpAction.SWITCH1

            self._eval_turn()
            self.turn += 1
            self.p1.decrease_switch_timer(1)
            self.p2.decrease_switch_timer(1)

        # Only one player fainted
        elif not (self.p1.is_active_alive and self.p2.is_active_alive):
            swap_timeout = SWITCH_TIMEOUT_TURNS
            while swap_timeout > 0 and (
                (self.p1.is_active_alive and self.p2_action == PvpAction.WAIT)
                or (self.p2.is_active_alive and self.p1_action == PvpAction.WAIT)
            ):
                self._eval_turn()
                self.turn += 1
                self.p1.decrease_switch_timer(1)
                self.p2.decrease_switch_timer(1)

                if self.p1.active_pokemon:
                    self.p1.decrease_cooldown()
                else:
                    self.p2.decrease_cooldown()

                self.p1_action = PvpAction.ACT_NULL
                self.p2_action = PvpAction.ACT_NULL
                self.p1_action = self.p1.decide_action(self.phase)
                self.p2_action = self.p2.decide_action(self.phase)
                swap_timeout -= 1

            if self.p1.is_active_alive and self.p2_action == PvpAction.WAIT:
                self.p2_action = PvpAction.SWITCH1
            if self.p2.is_active_alive and self.p1_action == PvpAction.WAIT:
                self.p1_action = PvpAction.SWITCH1

            self._eval_turn()
            self.turn += 1
            self.p1.decrease_switch_timer(1)
            self.p2.decrease_switch_timer(1)

            if self.p1.is_active_alive:
                self.p1.decrease_cooldown()
            else:
                self.p2.decrease_cooldown()

        assert self.p1.is_active_alive
        assert self.p2.is_active_alive

        self.phase = BattlePhase.NEUTRAL
        self.p1_action = PvpAction.ACT_NULL
        self.p2_action = PvpAction.ACT_NULL
        self.p1_action = self.p1.decide_action(self.phase)
        self.p2_action = self.p2.decide_action(self.phase)


class OneVsOneBattle:

    @classmethod
    def simulate(
        cls,
        attacker: PvpPokemon,
        defender: PvpPokemon,
        attacker_shields: int | None = None,
        defender_shields: int | None = None,
    ) -> int:
        """
        Simulates a battle between an attacker and a defender in a PvP scenario.

        Args:
            attacker (PvpPokemon): The attacking Pokemon.
            defender (PvpPokemon): The defending Pokemon.
            attacker_shields (int | None, optional): The number of shields the attacker has. Defaults to None.
            defender_shields (int | None, optional): The number of shields the defender has. Defaults to None.

        Returns:
            int: The battle rating of the attacker.
        """
        player_one = Player([attacker], shields=attacker_shields)
        player_two = Player([defender], shields=defender_shields)
        battle = PvpBattle(player_one, player_two)
        battle.simulate()
        return cls._get_battle_rating(attacker, defender)

    @staticmethod
    def _get_battle_rating(attacker: PvpPokemon, defender: PvpPokemon) -> int:
        """
        Calculate the battle rating based on the damage done to the opponent and the damage received.

        Args:
            attacker (PvpPokemon): The attacking Pokemon.
            defender (PvpPokemon): The defending Pokemon.

        Returns:
            int: The battle rating.
        """
        battle_rating = (
            500 * ((defender.full_hp - defender.hp) / defender.full_hp)
        ) + (500 * (attacker.hp / attacker.full_hp))
        return int(battle_rating)
