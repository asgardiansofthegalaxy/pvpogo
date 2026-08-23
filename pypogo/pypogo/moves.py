import json
import math
from enum import Enum
from functools import cached_property
from typing import Optional

from pypogo.constants import (
    CHARGE_DEFAULT_MOD,
    PVP_CHARGE_BONUS_MOD,
    PVP_FAST_BONUS_MOD,
    STAB_BONUS,
    TURN_TIME,
)

from .buff import MoveBuff
from .poketypes import PokeType


class Archetype(Enum):
    NONE = "None"
    GENERAL = "General"
    FAST_CHARGE = "Fast Charge"
    NUKE = "Nuke"
    LOW_QUALITY = "Low Quality"
    BOOST = "Boost"
    SPAM_BAIT = "Spam/Bait"
    MULTIPURPOSE = "Multipurpose"
    HIGH_ENERGY = "High Energy"
    HEAVY_DAMAGE = "Heavy Damage"
    BOOST_NUKE = "Boost Nuke"
    DEBUFF = "Debuff"
    SELF_DEBUFF = "Self-Debuff"
    DEBUFF_SPAM_BAIT = "Debuff Spam/Bait"
    BOOST_SPAM_BAIT = "Boost Spam/Bait"
    HIGH_ENERGY_DEBUFF = "High Energy Debuff"
    SELF_DEBUFF_NUKE = "Self-Debuff Nuke"


class MoveKind(Enum):
    CHARGED1 = 1
    CHARGED2 = 2
    FAST = 3


class Move:
    """
    Represents a base move a Pokémon can have.
    """

    def __init__(
        self,
        move_id: str = "",
        name: str = "",
        move_type: PokeType = PokeType.NONE,
        is_fast: bool = False,
        power: int = 0,
        energy: int = 0,
        energy_gain: int = 0,
        cooldown: int = 0,
        buff: Optional[MoveBuff] = None,
        archetype: Archetype = Archetype.NONE,
    ):
        """
        Initializes a new instance of the BaseMove class.

        Args:
            move_id (str): The ID of the move.
            name (str): The name of the move.
            move_type (PokeType): The type of the move.
            is_fast (bool): Indicates whether the move is a fast move or a charged move.
            power (int): The power of the move.
            energy (int): The energy cost of the move.
            energy_gain (int): The energy gain of the move.
            cooldown (int): The cooldown of the move in ms.
            buff (Buff): The buff associated with the move.
            archetype (str): The archetype of the move.
        """
        self.move_id = move_id
        self.name = name
        self.move_type = move_type
        self.is_fast = is_fast
        self.power = power
        self.energy = energy
        self.energy_gain = energy_gain
        self._cooldown = cooldown
        self._turns = cooldown / TURN_TIME
        self.buff = buff
        self.archetype = archetype

    @cached_property
    def dpe(self):
        """Calculates the damage per energy of the move."""
        return self.power / self.energy

    @property
    def cooldown_turns(self):
        """
        Gets the cooldown of the move in # of turns.

        Returns:
            int: The cooldown of the move.
        """
        return self._turns

    @property
    def is_self_debuff(self):
        """
        Indicates whether the move is a self-debuff move.

        Returns:
            bool: True if the move is a self-debuff move; otherwise, False.
        """
        return self.buff.atk_buff_self < 0 or self.buff.def_buff_self < 0

    def to_dict(self):
        """
        Converts the Move object to a dictionary.

        Returns:
            dict: The dict representation of the Move object.
        """
        return {
            "move_id": self.move_id,
            "name": self.name,
            "move_type": self.move_type.value,
            "is_fast": self.is_fast,
            "power": self.power,
            "energy": self.energy,
            "energy_gain": self.energy_gain,
            "cooldown": self._cooldown,
            "buff": self.buff.to_dict() if self.buff else None,
            "archetype": self.archetype.value,
        }

    def calculate_damage(self, attacker, defender):
        """
        Calculates the damage dealt by the move to the opponent.

        Args:
            attacker (Pokemon): The attacking Pokemon.
            defender (Pokemon): The defending Pokemon.

        Returns:
            int: The damage dealt by the move to the opponent.
        """
        stab = STAB_BONUS if self.move_type in attacker.types else 1.0

        bonus = (
            PVP_FAST_BONUS_MOD
            if self.is_fast
            else PVP_CHARGE_BONUS_MOD * CHARGE_DEFAULT_MOD
        )

        atk_stat = attacker.attack * attacker.buff_multiplier_atk
        def_stat = defender.defense * defender.buff_multiplier_def
        effectiveness = PokeType.get_damage_modifier(defender.types, self.move_type)

        damage = (
            math.floor(
                self.power * stab * (atk_stat / def_stat) * effectiveness * 0.5 * bonus
            )
            + 1
        )

        return damage

    def to_json(self):
        """
        Converts the Move object to a JSON string.

        Returns:
            str: The JSON representation of the Move object.
        """
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(data):
        """
        Creates a Move object from a JSON dict.

        Args:
            data (dict): The JSON dict representing the Move object.

        Returns:
            Move: The Move object created from the JSON string.
        """
        move_id = data.get("move_id", "")
        name = data.get("name", "")
        move_type = PokeType(data.get("move_type", PokeType.NONE.value))
        is_fast = data.get("is_fast", False)
        power = data.get("power", 0)
        energy = data.get("energy", 0)
        energy_gain = data.get("energy_gain", 0)
        cooldown = data.get("cooldown", 0)
        buff_dict = data.get("buff", None)
        buff = MoveBuff.from_dict(buff_dict) if buff_dict else None
        archetype = Archetype(data.get("archetype", Archetype.NONE.value))

        return Move(
            move_id=move_id,
            name=name,
            move_type=move_type,
            is_fast=is_fast,
            power=power,
            energy=energy,
            energy_gain=energy_gain,
            cooldown=cooldown,
            buff=buff,
            archetype=archetype,
        )


class PvpMove(Move):
    """
    Represents a move a Pokémon can have in PvP.
    """

    def __init__(self, move, attacker, defender):
        super().__init__(
            move_id=move.move_id,
            name=move.name,
            move_type=move.move_type,
            is_fast=move.is_fast,
            power=move.power,
            energy=move.energy,
            energy_gain=move.energy_gain,
            cooldown=move._cooldown,
            buff=move.buff,
            archetype=move.archetype,
        )
        self.attacker = attacker
        self.defender = defender

    @property
    def damage(self):
        """Calculates the damage dealt by the move to the opponent."""
        return self.calculate_damage(self.attacker, self.defender)
