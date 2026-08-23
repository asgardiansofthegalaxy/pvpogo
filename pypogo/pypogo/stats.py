import json
from dataclasses import dataclass
import math
from typing import List
from functools import cached_property, total_ordering

from .constants import CP_MULTIPLIER, MAX_IV, MAX_LEVEL


@dataclass
class Stats:
    """
    Represents the statistics of a Pokémon, including attack, defense, and stamina.
    """

    attack: int = 0
    defense: int = 0
    stamina: int = 0

    def to_dict(self):
        return {"attack": self.attack, "defense": self.defense, "stamina": self.stamina}

    def to_json(self):
        """
        Converts the Stats object to a JSON-compatible dictionary.

        Returns:
            dict: A dictionary representation of the Stats object.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        """
        Creates a Stats object from a JSON dict.

        Args:
            data (dict): A JSON dict containing the stats data.

        Returns:
            Stats: A Stats object initialized with the data from the dictionary.
        """
        return cls(
            attack=data.get("attack", 0),
            defense=data.get("defense", 0),
            stamina=data.get("stamina", 0),
        )


def get_cp_from_stats(base: Stats, ivs: Stats, level: float) -> int:
    """
    Calculate the Combat Power (CP) of a Pokémon based on its base stats, individual values (IVs), and level.

    Args:
        base (Stats): The base stats of the Pokémon.
        ivs (Stats): The individual values (IVs) of the Pokémon.
        level (float): The level of the Pokémon.

    Returns:
        int: The calculated CP of the Pokémon.
    """
    cp_multiplier = CP_MULTIPLIER[int((level - 1) * 2)]
    cp = max(
        math.floor(
            0.1
            * math.pow(cp_multiplier, 2)
            * (base.attack + ivs.attack)
            * math.sqrt((base.defense + ivs.defense) * (base.stamina + ivs.stamina))
        ),
        10,
    )
    return cp


@total_ordering
class StatsCombo:
    """
    Represents a combination of stats for a Pokémon.
    """

    def __init__(
        self,
        level: float = 0.0,
        base: Stats = Stats(),
        ivs: Stats = Stats(),
    ):
        self.level = level
        self.base = base or Stats()
        self.ivs = ivs or Stats()

    @cached_property
    def effective(self) -> Stats:
        cp_multiplier = CP_MULTIPLIER[int((self.level - 1) * 2)]
        return Stats(
            attack=int(cp_multiplier * (self.base.attack + self.ivs.attack)),
            defense=int(cp_multiplier * (self.base.defense + self.ivs.defense)),
            stamina=max(
                int(cp_multiplier * (self.base.stamina + self.ivs.stamina)),
                10,
            ),
        )

    def __str__(self) -> str:
        return f"CP: {self.cp}, Lvl: {self.level:.1f}, IVs: {self.ivs.attack}/{self.ivs.stamina}/{self.ivs.defense}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StatsCombo):
            return NotImplemented
        # Note: this used to return a tuple of comparisons, which is a
        # non-empty (and therefore always truthy) tuple, so every StatsCombo
        # compared equal to every other one.
        return (
            self.effective.attack == other.effective.attack
            and self.effective.defense == other.effective.defense
            and self.effective.stamina == other.effective.stamina
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.effective.attack,
                self.effective.defense,
                self.effective.stamina,
            )
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, StatsCombo):
            return NotImplemented
        return (
            self.effective.attack + self.effective.defense + self.effective.stamina
            < other.effective.attack + other.effective.defense + other.effective.stamina
        )


class StatsRanker:

    @staticmethod
    def _rank_ivs(base: Stats, max_cp: int):
        """
        Ranks all possible IV combinations for a given base stats and maximum CP.

        Args:
            base (Stats): The base stats of the Pokémon.
            max_cp (int): The maximum CP allowed.

        Returns:
            list: A list of StatsCombo objects representing the ranked IV combinations.
        """
        rankings = []
        ivs = Stats(0, 0, 0)
        possible_levels = [level / 2 for level in range(2, int(MAX_LEVEL * 2) + 2)]

        for level in possible_levels:
            for ivs.attack in range(MAX_IV + 1):
                for ivs.stamina in range(MAX_IV + 1):
                    for ivs.defense in range(MAX_IV + 1):
                        cp = get_cp_from_stats(base, ivs, level)
                        if cp <= max_cp:
                            rankings.append(
                                StatsCombo(
                                    cp=cp,
                                    level=level,
                                    base=base,
                                    ivs=Stats(ivs.attack, ivs.defense, ivs.stamina),
                                )
                            )

        return rankings

    @staticmethod
    def get_iv_rankings(
        base: Stats, max_cp: int = None, limit: int = None
    ) -> List[StatsCombo]:
        """
        Ranks the IV combinations by effective stats output.

        Args:
            base (Stats): The base Pokemon's stats.
            max_cp (int, optional): The maximum CP to rank IV combinations for. Defaults to None.
            limit (int, optional): The maximum number of IV combinations to return. Defaults to None.

        Returns:
            List[StatsCombo]: A list of ranked IV combinations.
        """
        if not max_cp:
            max_cp = get_cp_from_stats(base, Stats(MAX_IV, MAX_IV, MAX_IV), MAX_LEVEL)

        rankings: List[StatsCombo] = StatsRanker._rank_ivs(base, max_cp)

        # Sort the rankings by effective stats
        rankings.sort(reverse=True)

        if limit and limit < len(rankings):
            rankings = rankings[:limit]

        return rankings
