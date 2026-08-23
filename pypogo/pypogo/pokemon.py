import json
from typing import List
from functools import cached_property

from .buff import BuffState, BUFF_MULTIPLIER
from .constants import (
    CP_MULTIPLIER,
    MAX_LEVEL,
    MAX_IV,
)
from .pokedex import PokedexEntry
from .stats import Stats, get_cp_from_stats
from .moves import Move, MoveKind


class Pokemon:
    def __init__(
        self,
        pdex_mon: PokedexEntry,
        level: float,
        ivs: Stats,
        fast_move: Move,
        charged_moves: List[Move],
    ):
        if not 0 <= level <= MAX_LEVEL:
            raise ValueError(f"Invalid level: Level must be between 0 and {MAX_LEVEL}")
        if not 0 <= ivs.attack <= MAX_IV:
            raise ValueError(
                f"Invalid attack IV: Attack IV must be between 0 and {MAX_IV}"
            )
        if not 0 <= ivs.defense <= MAX_IV:
            raise ValueError(
                f"Invalid defense IV: Defense IV must be between 0 and {MAX_IV}"
            )
        if not 0 <= ivs.stamina <= MAX_IV:
            raise ValueError(
                f"Invalid stamina IV: Stamina IV must be between 0 and {MAX_IV}"
            )
        if not fast_move.move_id in pdex_mon.fast_moves:
            raise ValueError(
                "Invalid fast move: Fast move is not valid for this Pokémon"
            )
        if not all(
            map(lambda move: move.move_id in pdex_mon.charged_moves, charged_moves)
        ):
            raise ValueError(
                "Invalid charged moves: Charged moves are not valid for this Pokémon"
            )

        self.pdex_mon = pdex_mon
        self.level = level
        self.ivs = ivs
        self.fast_move = fast_move
        self.charged_moves = charged_moves
        self.base_stats = self.pdex_mon.base_stats
        self.types = self.pdex_mon.types
        self._hp = max(
            int(self.cp_multiplier * (self.ivs.stamina + self.base_stats.stamina)), 10
        )
        self._full_hp = self._hp

    @property
    def fastest_charged_move(self) -> Move:
        """
        Returns the fastest (lowest energy) charged move of the Pokémon.

        Returns:
            Move: The fastest charged move of the Pokémon.
        """
        return min(self.charged_moves, key=lambda move: move.energy)

    @property
    def best_charged_move(self) -> Move:
        """
        Returns the best (highest damage) charged move of the Pokémon.

        Returns:
            Move: The best charged move of the Pokémon.
        """
        # TODO: Improve this logic
        return max(self.charged_moves, key=lambda move: move.damage)

    @property
    def active_charged_moves(self) -> List[Move]:
        """
        Returns the active charged moves of the Pokémon.

        Returns:
            List[Move]: The active charged moves of the Pokémon.
        """
        return [move for move in self.charged_moves if move.energy <= self.energy]

    @property
    def full_hp(self) -> int:
        """
        Returns the full hit points (HP) of the Pokémon.

        Returns:
            int: The full hit points (HP) of the Pokémon.
        """
        return self._full_hp

    @cached_property
    def attack(self) -> int:
        """
        Calculates and returns the attack value of the Pokémon.

        Returns:
            int: The attack value of the Pokémon.
        """
        return int(self.cp_multiplier * (self.base_stats.attack + self.ivs.attack))

    @cached_property
    def defense(self) -> int:
        """
        Calculates and returns the defense value of the Pokémon.

        Returns:
            int: The defense value of the Pokémon.
        """
        return int(self.cp_multiplier * (self.base_stats.defense + self.ivs.defense))

    @cached_property
    def stamina(self) -> int:
        """
        Calculates and returns the stamina value of the Pokémon.

        Returns:
            int: The stamina value of the Pokémon.
        """
        return max(
            int(self.cp_multiplier * (self.base_stats.stamina + self.ivs.stamina)), 10
        )

    @cached_property
    def cp(self) -> int:
        """
        Calculates and returns the combat power (CP) of the Pokémon.

        Returns:
            int: The combat power (CP) of the Pokémon.
        """
        return get_cp_from_stats(self.base_stats, self.ivs, self.level)

    @property
    def hp(self) -> int:
        """
        Returns the hit points (HP) of the Pokémon.

        Returns:
            int: The hit points (HP) of the Pokémon.
        """
        return self._hp

    @hp.setter
    def hp(self, new_hp):
        """
        Sets the hit points (HP) of the Pokémon.
        """
        self._hp = new_hp

    @property
    def cp_multiplier(self) -> float:
        """
        Returns the Combat Power (CP) Multiplier for the current level of the Pokemon.

        The CP Multiplier is a value used to calculate the CP of a Pokemon based on its level.
        It is determined by the Pokemon's level and is stored in a lookup table.

        Returns:
            float: The CP Multiplier for the current level of the Pokemon.
        """
        return CP_MULTIPLIER[int((self.level - 1) * 2)]

    @property
    def is_alive(self) -> bool:
        """
        Checks if the Pokémon is alive.

        Returns:
            bool: True if the Pokémon is alive, False otherwise.
        """
        return bool(self._hp)

    def get_move(self, move_kind: MoveKind) -> Move:
        """
        Retrieves the move of the specified type for the Pokemon.

        Args:
            move_kind (MoveKind): The kind of move to retrieve.

        Returns:
            Move: The move of the specified type.
        """

        if move_kind == MoveKind.FAST:
            return self.fast_move
        elif move_kind == MoveKind.CHARGED1:
            return self.charged_moves[0]
        elif move_kind == MoveKind.CHARGED2:
            return self.charged_moves[-1]
        else:
            raise ValueError(f"Invalid move type {move_kind}")

    def to_dict(self):
        """
        Converts the PvpPokemon object to a dict.

        Returns:
            dict: The dict representation of the PvpPokemon object.
        """
        return {
            "pdex_mon": self.pdex_mon.to_dict(),
            "level": self.level,
            "ivs": self.ivs.to_dict(),
            "fast_move": self.fast_move.to_dict(),
            "charged_moves": [move.to_dict() for move in self.charged_moves],
        }

    def to_json(self):
        """
        Converts the PvpPokemon object to a JSON string.

        Returns:
            str: The JSON representation of the PvpPokemon object.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        """
        Creates a PvpPokemon object from a JSON dict.

        Args:
            data (dict): The JSON dict representing the PvpPokemon object.

        Returns:
            PvpPokemon: The PvpPokemon object created from the JSON string.
        """
        pdex_mon = PokedexEntry.from_dict(data["pdex_mon"])
        level = data["level"]
        ivs = Stats.from_dict(data["ivs"])
        fast_move = Move.from_dict(data["fast_move"])
        charged_moves = [Move.from_dict(move) for move in data["charged_moves"]]

        return cls(
            pdex_mon=pdex_mon,
            level=level,
            ivs=ivs,
            fast_move=fast_move,
            charged_moves=charged_moves,
        )


class PvpPokemon(Pokemon):
    """
    Represents a Pokémon for PvP battles.
    """

    def __init__(
        self,
        pdex_mon: PokedexEntry,
        level: float,
        ivs: Stats,
        fast_move: Move,
        charged_moves: List[Move],
    ):
        """
        Initializes a PvpPokemon object.
        """
        super().__init__(
            pdex_mon=pdex_mon,
            level=level,
            ivs=ivs,
            fast_move=fast_move,
            charged_moves=charged_moves,
        )
        self._cooldown = 0
        self.energy = 0
        self.buffs = BuffState()

    @property
    def cooldown_turns(self) -> int:
        """
        Returns the cooldown (in # of turns) of the Pokémon.

        Returns:
            int: The cooldown of the Pokémon.
        """
        return self._cooldown

    @cooldown_turns.setter
    def cooldown_turns(self, value):
        """
        Sets the cooldown of the Pokémon.
        """
        self._cooldown = value

    @property
    def buff_multiplier_atk(self):
        """
        Returns the attack multiplier based on the current attack buff level.

        Returns:
            float: The attack buff multiplier.
        """
        return BUFF_MULTIPLIER[self.buffs.atk_buff_lvl.value]

    @property
    def buff_multiplier_def(self):
        """
        Returns the defense buff multiplier based on the current defense buff level.

        Returns:
            float: The defense buff multiplier.
        """
        return BUFF_MULTIPLIER[self.buffs.def_buff_lvl.value]

    def calculate_damage(self, move_kind: MoveKind, opponent: Pokemon) -> int:
        """
        Calculates the damage dealt by the move to the opponent.

        Args:
            move (MoveKind): The type of move to calculate damage for.
            opponent (Pokemon): The opponent to calculate damage against.

        Returns:
            int: The damage dealt by the move to the opponent.
        """
        move = self.get_move(move_kind)
        return move.calculate_damage(attacker=self, defender=opponent)

    def calculate_potential_damage(
        self, opponent: Pokemon, stored_energy: int, stack: bool = True
    ) -> int:
        """
        Calculates the potential damage dealt by the charged moves to the opponent.

        Args:
            opponent (Pokemon): The opponent to calculate damage against.
            stored_energy (int): The amount of stored energy by the opponent.
            stack (bool): Indicates whether to stack the charged move damage.

        Returns:
            int: The potential damage dealt by the charged moves to the opponent.
        """
        total_damage = [0]

        for move in self.charged_moves:
            count_multiplier = stored_energy // move.energy if stack else 0
            if not stack and move.energy <= stored_energy:
                count_multiplier = 1

            damage = count_multiplier * move.calculate_damage(self, opponent)
            total_damage.append(damage)

        return max(total_damage)

    def full_reset(self):
        """
        Fully resets the Pokémon's state.
        """
        self._hp = self.full_hp
        self._cooldown = 0
        self.energy = 0
        self.buffs = BuffState()

    def clone(self):
        """
        Creates a deep copy of the Pokémon, with its stats reset.

        Returns:
            PvpPokemon: The deep copy of the Pokémon.
        """
        pokemon = PvpPokemon.from_dict(self.to_dict())
        pokemon.full_reset()
        return pokemon

    def __repr__(self) -> str:
        return f"{self.pdex_mon.species_id}"
