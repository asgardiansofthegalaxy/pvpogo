from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pypogo.action import PvpAction
from pypogo.constants import BattlePhase

if TYPE_CHECKING:
    from pypogo.player import Player


class AIStatus(Enum):
    AI_NULL_STATUS = 0
    AI_SUCCESS = 1
    AI_ERROR_FAIL = 2
    AI_ERROR_BAD_VALUE = 3
    AI_ERROR_NOMEM = 4

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, AIStatus):
            return NotImplemented
        return self.value == __value.value

    def __hash__(self) -> int:
        # Defining __eq__ sets __hash__ to None, which would make members
        # unusable as dict keys or set elements.
        return hash(self.value)


class AInterface(ABC):
    """
    Contract every battle AI implements.

    Implementations get their own player via `self.player`. Battle context the
    heuristics need -- the opposing player and the current turn -- is reached
    through the `opponent` and `turn` helpers below rather than being passed
    into every call, so `PvpBattle` can keep calling `decide_action(phase)`.
    """

    #: Set by each implementation's __init__. Declared here because the
    #: helpers and is_valid_action below all read through it.
    player: "Player"

    @property
    def opponent(self) -> Optional["Player"]:
        """The opposing Player, or None outside of a battle."""
        return getattr(self.player, "opponent", None)

    @property
    def turn(self) -> int:
        """The current battle turn, or 0 outside of a battle."""
        battle = getattr(self.player, "battle", None)
        return battle.turn if battle is not None else 0

    @abstractmethod
    def select_team(
        self,
        previous_teams=None,
        previous_result: Optional[str] = None,
        selection_strategy=None,
    ):
        pass

    @abstractmethod
    def decide_action(self, battle_phase):
        """Return a (AIStatus, PvpAction) pair for the given phase."""

    @abstractmethod
    def decide_switch(self):
        pass

    @abstractmethod
    def decide_shield(self):
        pass

    def is_valid_action(self, action, battle_phase) -> bool:
        """
        Checks if the given action is valid for the player in the current battle phase.

        Args:
            action (PvpAction): The action to be validated.
            battle_phase (BattlePhase): The current battle phase.

        Returns:
            bool: True if the action is valid, False otherwise.
        """
        if battle_phase == BattlePhase.GAME_OVER:
            return False

        if action.is_fast:
            return battle_phase == BattlePhase.NEUTRAL and self.player.is_active_alive and not self.player.has_cooldown

        elif action.is_charged:
            if battle_phase != BattlePhase.NEUTRAL or not self.player.is_active_alive or self.player.has_cooldown:
                return False
            move_index = 0 if action == PvpAction.CHARGED1 else 1
            energy_required = self.player.active_pokemon.charged_moves[
                move_index
            ].energy

            return energy_required <= self.player.active_pokemon.energy
        
        elif action == PvpAction.SHIELD:
            return (
                battle_phase == BattlePhase.SUSPEND_CHARGED and self.player.shields > 0
            )

        elif action == PvpAction.WAIT:
            return self.player.is_active_alive

        elif action == PvpAction.SWITCH1:
            return self.player.get_remaining_pokemon() > int(
                self.player.is_active_alive and not self.player.has_switch_timer
            )

        elif action == PvpAction.SWITCH2:
            return (
                self.player.get_remaining_pokemon()
                > int(self.player.is_active_alive) + 1
                and not self.player.has_switch_timer
            )

        return False
