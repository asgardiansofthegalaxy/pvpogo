from typing import List

from pypogo.ai import AIStatus
from pypogo.moves import MoveKind

from .ai.naive import NaiveAI
from .pokemon import PvpPokemon
from .buff import BuffState
from .action import PvpAction


class Player:
    """
    Represents a player in the game.
    """

    def __init__(self, team: List[PvpPokemon], shields=None, ai=None, name=None):
        """
        Initializes a Player object.
        """
        self.ai = ai if ai else NaiveAI(self)
        self.team = team
        self.roster = team
        self.name = name
        self._active_pokemon_idx = 0
        self._starting_shields = 2 if shields is None else shields
        self._shields = self._starting_shields
        self.switch_timer = 0
        self._shields_used = 0
        self.opponent: "Player" = None
        self.battle = None

    def enter_battle(self, battle, opponent: "Player"):
        """
        Attach this player to a battle.

        Args:
            battle (PvpBattle): The battle this player is taking part in.
            opponent (Player): The player on the other side of it.
        """
        self.battle = battle
        self.opponent = opponent

    @property
    def starting_shields(self) -> int:
        """
        Get the number of starting shields the player has.

        Returns:
            int: The number of starting shields.
        """
        return self._starting_shields

    @property
    def shields_used(self) -> int:
        """
        Get the number of shields the player has used.

        Returns:
            int: The number of shields used.
        """
        return self._shields_used

    @property
    def shields(self) -> int:
        """
        Get the number of shields the player has.

        Returns:
            int: The number of shields the player has.
        """
        return self._shields

    @property
    def active_pokemon(self) -> PvpPokemon:
        """
        Get the active Pokemon.

        Returns:
            PvpPokemon: The active Pokemon.
        """
        assert 0 <= self._active_pokemon_idx <= 2
        return self.team[self._active_pokemon_idx]

    @property
    def has_switch_timer(self) -> bool:
        """
        Check if the player has a switch timer.

        Returns:
            bool: True if the player has a switch timer, False otherwise.
        """
        return self.switch_timer > 0

    @property
    def can_switch(self) -> bool:
        """
        Check if the player can switch Pokemon.

        Returns:
            bool: True if the player can switch Pokemon, False otherwise.
        """
        return not self.is_active_alive or not self.has_switch_timer

    @property
    def has_cooldown(self) -> bool:
        """
        Check if the active Pokemon has a cooldown.

        Returns:
            bool: True if the active Pokemon has a cooldown, False otherwise.
        """
        return self.get_cooldown() > 0

    def decide_action(self, battle_phase) -> PvpAction:
        """
        Decide the action in a player versus player battle.

        Returns:
            PvpAction: The action to be taken by the player.
        """
        result, action = self.ai.decide_action(battle_phase)

        assert result == AIStatus.AI_SUCCESS
        return action

    def start_switch_timer(self, switch_turns: int):
        """
        Start the switch timer.

        Args:
            switch_turns (int): The number of turns for the switch timer.
        """
        self.switch_timer = switch_turns

    def decrease_switch_timer(self, amount: int):
        """
        Decreases the switch timer by the specified amount.

        Args:
            amount (int): The amount to decrease the switch timer by.

        Returns:
            None
        """
        self.switch_timer = max(self.switch_timer - amount, 0)

    def decrease_cooldown(self, cooldown_delta: int = 1):
        """
        Decrease the cooldown of the active Pokemon.

        Args:
            delta_turns (int): The number of turns to decrease the cooldown by.
        """
        self.active_pokemon.cooldown_turns = max(
            self.active_pokemon.cooldown_turns - cooldown_delta, 0
        )

    def increase_cooldown(self, delta_turns: int = 0):
        """
        Increase the cooldown of the active Pokemon.

        Args:
            delta_turns (int): The number of turns to increase the cooldown by.
        """
        self.active_pokemon.cooldown_turns += delta_turns

    def get_cooldown(self) -> int:
        """
        Get the cooldown of the active Pokemon.

        Returns:
            int: The cooldown of the active Pokemon.
        """
        return self.active_pokemon.cooldown_turns

    @property
    def is_active_alive(self) -> bool:
        """
        Check if the active Pokemon is alive.

        Returns:
            bool: True if the active Pokemon is alive, False otherwise.
        """
        return self.active_pokemon.is_alive

    def increase_energy(self, delta: int):
        """
        Increase the energy of the active Pokemon.

        Args:
            delta (int): The amount of energy to increase.
        """
        self.active_pokemon.energy += delta

    def decrease_energy(self, delta: int):
        """
        Decrease the energy of the active Pokemon.

        Args:
            delta (int): The amount of energy to decrease.
        """
        self.active_pokemon.energy = max(self.active_pokemon.energy - delta, 0)

    def receive_damage(self, damage: int):
        """
        Reduces the HP of the active Pokemon by the specified amount of damage.

        Args:
            damage (int): The amount of damage to be inflicted on the active Pokemon.
        """
        self.active_pokemon.hp = max(self.active_pokemon.hp - damage, 0)

    def get_remaining_pokemon(self) -> int:
        """
        Get the number of remaining Pokemon in the team.

        Returns:
            int: The number of remaining Pokemon in the team.
        """
        return sum(bool(pokemon.hp) for pokemon in self.team)

    def use_shield(self):
        """
        Use a shield.

        Args:
            player (Player): The player to use the shield on.
        """
        if self._shields > 0:
            self._shields -= 1
            self._shields_used += 1

    def do_switch(self, first_available: bool):
        """
        Switches the active Pokemon in the player's team.

        Args:
            first_available (bool): Indicates whether it is the first available
            switch or not.

        Returns:
            None
        """
        for i, pokemon in enumerate(self.team):
            if self._active_pokemon_idx == i or pokemon.hp <= 0:
                continue

            if first_available:
                self._active_pokemon_idx = i
                self.active_pokemon.buffs = BuffState()
                break
            else:
                first_available = True

    def do_fast(self, defender):
        """
        Perform a fast move on the opponent.

        Args:
            defender (Player): The defending player.

        Returns:
            None
        """
        damage = self.active_pokemon.calculate_damage(
            MoveKind.FAST, defender.active_pokemon
        )

        defender.receive_damage(damage)
        self.increase_cooldown(self.active_pokemon.fast_move.cooldown_turns)
        self.increase_energy(self.active_pokemon.fast_move.energy_gain)

    def reset_team(self):
        for pokemon in self.team:
            pokemon.full_reset()

    def __repr__(self) -> str:
        return f"Player {self.name} - Team: {self.team}"
