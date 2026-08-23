import json
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import List, Optional

from .poketypes import PokeType
from .regions import REGIONAL_DEX_NUMBERS, REGIONS, UNKNOWN_REGION, Region
from .stats import Stats


class PokedexTags(Enum):
    NONE = "none"
    LEGENDARY = "legendary"
    MYTHICAL = "mythical"
    MEGA = "mega"
    SHADOW_ELIGIBLE = "shadoweligible"
    SHADOW = "shadow"
    PURE = "pure"
    ALOLAN = "alolan"
    GALARIAN = "galarian"
    STARTER = "starter"
    REGIONAL = "regional"
    HISUIAN = "hisuian"


@dataclass
class PokemonFamily:
    family_id: str
    parent: Optional[str] = None
    evolutions: List[str] = field(default_factory=list)


class PokedexEntry:
    def __init__(
        self,
        dex_number: int,
        species_name: str,
        species_id: str,
        family: PokemonFamily,
        types: List[PokeType],
        base_stats: Stats,
        tags: List[PokedexTags],
        fast_moves: List[str],
        charged_moves: List[str],
        buddy_distance: int,
        third_move_cost: Optional[int] = None,
    ):
        self.dex_number = dex_number
        self.species_name = species_name
        self.species_id = species_id
        self.family = family
        self.types = types
        self.base_stats = base_stats
        self.tags = tags
        self.fast_moves = fast_moves
        self.charged_moves = charged_moves
        self.buddy_distance = buddy_distance
        self.third_move_cost = third_move_cost

    def __str__(self):
        return f"PokedexMon(number={self.dex_number}, name='{self.name}', form_name='{self.form_name}')"

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, PokedexEntry):
            return (
                self.dex_number == __value.dex_number
                and self.species_name == __value.species_name
                and self.species_id == __value.species_id
            )
        return False

    def __hash__(self) -> int:
        # Keep instances hashable now that __eq__ is defined; mirrors the
        # fields __eq__ compares.
        return hash((self.dex_number, self.species_name, self.species_id))

    @classmethod
    def from_dict(cls, data):
        """
        Creates a PokedexEntry object from a JSON dict.

        Args:
            data (dict): The JSON dict representing the PokedexEntry object.

        Returns:
            PokedexEntry: The PokedexEntry object created from the JSON string.
        """
        dex_number = data["dex_number"]
        species_name = data["species_name"]
        species_id = data["species_id"]
        family_data = data["family"]
        family_id = family_data["family_id"]
        parent = family_data["parent"]
        evolutions = family_data["evolutions"]
        types = [PokeType(t) for t in data["types"]]
        base_stats_data = data["base_stats"]
        base_stats = Stats(
            attack=base_stats_data["attack"],
            defense=base_stats_data["defense"],
            stamina=base_stats_data["stamina"],
        )
        tags = [PokedexTags(tag) for tag in data["tags"]]
        fast_moves = data["fast_moves"]
        charged_moves = data["charged_moves"]
        buddy_distance = data["buddy_distance"]
        third_move_cost = data["third_move_cost"]

        return cls(
            dex_number=dex_number,
            species_name=species_name,
            species_id=species_id,
            family=PokemonFamily(
                family_id=family_id, parent=parent, evolutions=evolutions
            ),
            types=types,
            base_stats=base_stats,
            tags=tags,
            fast_moves=fast_moves,
            charged_moves=charged_moves,
            buddy_distance=buddy_distance,
            third_move_cost=third_move_cost,
        )

    def to_dict(self):
        """
        Converts the DexEntry object to a dict.

        Returns:
            dict: The dict representation of the DexEntry object.
        """
        return {
            "dex_number": self.dex_number,
            "species_name": self.species_name,
            "species_id": self.species_id,
            "family": {
                "family_id": self.family.family_id,
                "parent": self.family.parent,
                "evolutions": self.family.evolutions,
            },
            "types": [t.value for t in self.types],
            "base_stats": {
                "attack": self.base_stats.attack,
                "defense": self.base_stats.defense,
                "stamina": self.base_stats.stamina,
            },
            "tags": [str(tag) for tag in self.tags],
            "fast_moves": self.fast_moves,
            "charged_moves": self.charged_moves,
            "buddy_distance": self.buddy_distance,
            "third_move_cost": self.third_move_cost,
        }

    def to_json(self):
        """
        Converts the DexEntry object to a JSON string.

        Returns:
            str: The JSON representation of the DexEntry object.
        """
        return json.dumps(self.to_dict())

    @cached_property
    def region(self) -> Region:
        """
        Returns the region of the Pokémon based on its Pokédex number.

        Returns:
            Region: The region of the Pokémon.
        """
        for region in REGIONS.values():
            if (
                region != UNKNOWN_REGION
                and region.dex_start <= self.dex_number <= region.dex_end
            ):
                return region
        return UNKNOWN_REGION

    def is_starter(self) -> bool:
        """
        Checks if a given Pokémon's Pokédex number corresponds to a starter Pokémon.

        Returns:
            bool: True if the Pokémon is a starter Pokémon, False otherwise.
        """
        # Skip "Unknown" region
        for region in REGIONS.values():
            if (
                region != UNKNOWN_REGION
                and region.dex_start <= self.dex_number < region.dex_start + 9
            ):
                return True
        return False

    def is_regional(self) -> bool:
        """
        Check if a given Pokémon dex number is regional.

        Returns:
            bool: True if the dex number is regional, False otherwise.
        """
        # TODO: This can be improved
        return self.dex_number in REGIONAL_DEX_NUMBERS
