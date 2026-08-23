import json
from enum import Enum
from functools import cached_property

from .constants import BUFF_MULTIPLIER


class BuffTarget(Enum):
    NONE = "none"
    SELF = "self"
    OPPONENT = "opponent"
    BOTH = "both"


class BuffLevel(Enum):
    """
    Enum representing the different levels of buffs for attack and defense.

    No buff means 4/4 damage = 100%.
    Each boost stage (to either attack or defense) increases the first number - so 5/4, 6/4, 7/4, 8/4. (125%, 150%, 175%, 200%)
    Each debuff stage is increasing the second number - 4/5, 4/6, 4/7, 4/8 (80%, 66%, 57%, 50%)
    """

    B_4_8 = -4  # Max debuff
    B_4_7 = -3
    B_4_6 = -2
    B_4_5 = -1
    B_4_4 = 0  # No buff
    B_5_4 = 1
    B_6_4 = 2
    B_7_4 = 3
    B_8_4 = 4  # Max buff


class MoveBuff:
    """
    Represents the buff of a move that can be applied to a Pokemon.
    """

    def __init__(
        self,
        chance: float,
        atk_buff_self: int,
        def_buff_self: int,
        atk_buff_opponent: int,
        def_buff_opponent: int,
    ):
        self.chance = chance
        self.atk_buff_self = atk_buff_self
        self.def_buff_self = def_buff_self
        self.atk_buff_opponent = atk_buff_opponent
        self.def_buff_opponent = def_buff_opponent

    @cached_property
    def target(self):
        buff_self = False
        buff_opponent = False
        if any(self.atk_buff_self, self.def_buff_self):
            buff_self = True
        if any(self.atk_buff_opponent, self.def_buff_opponent):
            buff_opponent = True

        if all(buff_self, buff_opponent):
            return BuffTarget.BOTH
        elif buff_self:
            return BuffTarget.SELF
        elif buff_opponent:
            return BuffTarget.OPPONENT
        else:
            return BuffTarget.NONE

    def to_dict(self):
        """
        Converts the Buff object to a dictionary.

        Returns:
            dict: The dictionary representation of the Buff object.
        """
        return {
            "chance": self.chance,
            "atk_buff_self": self.atk_buff_self,
            "def_buff_self": self.def_buff_self,
            "atk_buff_opponent": self.atk_buff_opponent,
            "def_buff_opponent": self.def_buff_opponent,
        }

    def to_json(self):
        """
        Converts the Buff object to a JSON string.

        Returns:
            str: The JSON representation of the Buff object.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        """
        Creates a BuffState object from a JSON dict.

        Parameters:
            data (dict): The JSON dict representing the BuffState object.

        Returns:
            BuffState: The BuffState object created from the JSON string.
        """
        chance = data["chance"]
        atk_buff_self = BuffLevel(data["atk_buff_self"])
        def_buff_self = BuffLevel(data["def_buff_self"])
        atk_buff_opponent = BuffLevel(data["atk_buff_opponent"])
        def_buff_opponent = BuffLevel(data["def_buff_opponent"])
        return cls(
            chance=chance,
            atk_buff_self=atk_buff_self,
            def_buff_self=def_buff_self,
            atk_buff_opponent=atk_buff_opponent,
            def_buff_opponent=def_buff_opponent,
        )


class BuffState:
    """
    Represents the state of buffs for a Pokemon.
    """

    def __init__(
        self,
        atk_buff_lvl: BuffLevel = BuffLevel.B_4_4,
        def_buff_lvl: BuffLevel = BuffLevel.B_4_4,
    ) -> None:
        """
        Initializes a new instance of the BuffState class.

        Parameters:
            atk_buff_lvl (BuffLevel): The attack buff level. Default is BuffLevel.B_4_4.
            def_buff_lvl (BuffLevel): The defense buff level. Default is BuffLevel.B_4_4.
        """
        self.atk_buff_lvl = atk_buff_lvl
        self.def_buff_lvl = def_buff_lvl

    def debuff_attack(self, amount: int) -> BuffLevel:
        """
        Decreases the attack buff level by the specified amount.

        Parameters:
            amount (int): The amount to decrease the attack buff level by.

        Returns:
            BuffLevel: The new attack buff level after the decrease.
        """
        return BuffLevel(max(BuffLevel.B_4_8.value, self.atk_buff_lvl.value - amount))

    def debuff_defense(self, amount: int) -> BuffLevel:
        """
        Decreases the defense buff level by the specified amount.

        Parameters:
            amount (int): The amount to decrease the defense buff level by.

        Returns:
            BuffLevel: The new defense buff level after the decrease.
        """
        return BuffLevel(max(BuffLevel.B_4_8.value, self.def_buff_lvl.value - amount))

    def buff_attack(self, amount: int) -> BuffLevel:
        """
        Increases the attack buff level by the specified amount.

        Parameters:
            amount (int): The amount to increase the attack buff level by.

        Returns:
            BuffLevel: The new attack buff level after the increase.
        """
        return BuffLevel(min(BuffLevel.B_8_4.value, self.atk_buff_lvl.value + amount))

    def buff_defense(self, amount: int) -> BuffLevel:
        """
        Increases the defense buff level by the specified amount.

        Parameters:
            amount (int): The amount to increase the defense buff level by.

        Returns:
            BuffLevel: The new defense buff level after the increase.
        """
        return BuffLevel(min(BuffLevel.B_8_4.value, self.def_buff_lvl.value + amount))

    @property
    def attack_multiplier(self) -> float:
        """
        Calculates the attack multiplier based on the current attack buff level.

        Returns:
            float: The attack multiplier.
        """
        return BUFF_MULTIPLIER[self.atk_buff_lvl.value + 4]

    @property
    def defense_multiplier(self) -> float:
        """
        Calculates the defense multiplier based on the current defense buff level.

        Returns:
            float: The defense multiplier.
        """
        return BUFF_MULTIPLIER[self.def_buff_lvl.value + 4]
