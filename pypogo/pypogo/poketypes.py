from enum import Enum
from dataclasses import dataclass
from typing import List

from pypogo.damage_modifiers import DAMAGE_MODIFIERS


class PokeType(Enum):
    """
    Represents a Pokémon type.
    """

    NONE = "none"
    BUG = "bug"
    DARK = "dark"
    DRAGON = "dragon"
    ELECTRIC = "electric"
    FAIRY = "fairy"
    FIGHTING = "fighting"
    FIRE = "fire"
    FLYING = "flying"
    GHOST = "ghost"
    GRASS = "grass"
    GROUND = "ground"
    ICE = "ice"
    NORMAL = "normal"
    POISON = "poison"
    PSYCHIC = "psychic"
    ROCK = "rock"
    STEEL = "steel"
    WATER = "water"

    def is_weak(self, poke_type: object):
        """
        Check if this type is weak against the given Pokémon type.

        Args:
            poke_type (object): The Pokémon type to check against.

        Returns:
            bool: True if this type is weak against the given type, False otherwise.
        """
        return poke_type in POKE_TYPE_TRAITS_DICT[self].weaknesses

    def resists(self, poke_type: object):
        """
        Check if this type resists the given Pokémon type.

        Args:
            poke_type (object): The Pokémon type to check against.

        Returns:
            bool: True if this type resists the given type, False otherwise.
        """
        return poke_type in POKE_TYPE_TRAITS_DICT[self].resistances

    def is_immunte(self, poke_type: object):
        """
        Check if this type is immune to the given Pokémon type.

        Args:
            poke_type (object): The Pokémon type to check against.

        Returns:
            bool: True if this type is immune to the given type, False otherwise.
        """
        return poke_type in POKE_TYPE_TRAITS_DICT[self].immunities

    @property
    def index(self):
        """
        Get the index of this type.

        Returns:
            int: The index of this type.
        """
        return TYPE_INDEX_MAP[self.name]

    @staticmethod
    def get_damage_modifier(def_types: List[object], atk_type: object):
        """
        Get the damage modifier for the given attacking and defending types.

        Args:
            def_types (list[PokeType]): The defending types.
            atk_type (Poketype): The attacking type.
        Returns:
            float: The damage modifier for the given attacking and defending types.
        """
        count = len(def_types)
        try:
            if count == 2:
                type1, type2 = def_types
                return DAMAGE_MODIFIERS[type1.index - 1][type2.index][
                    atk_type.index - 1
                ]
            elif count == 1:
                type1 = def_types.pop()
                return DAMAGE_MODIFIERS[type1.index - 1][0][atk_type.index - 1]
            else:
                raise ValueError(f"Error: Received wrong number of types ({count})")
        except IndexError:
            raise ValueError(
                f"Error: Received invalid type index ({type1.name}:{type1.index}, {type2.name}:{type2.index}, {atk_type.name}:{atk_type.index})"
            )


@dataclass
class PokeTypeTraits:
    resistances: set
    weaknesses: set
    immunities: set


TYPE_INDEX_MAP = {
    poke_type: index for index, poke_type in enumerate(PokeType._member_names_)
}


POKE_TYPE_TRAITS_DICT = {
    PokeType.NONE: PokeTypeTraits(PokeType.NONE, PokeType.NONE, PokeType.NONE),
    PokeType.BUG: PokeTypeTraits(
        {PokeType.FIGHTING, PokeType.GROUND, PokeType.GRASS},
        {PokeType.FLYING, PokeType.ROCK, PokeType.FIRE},
        PokeType.NONE,
    ),
    PokeType.DARK: PokeTypeTraits(
        {PokeType.GHOST, PokeType.DARK},
        {PokeType.FIGHTING, PokeType.FAIRY, PokeType.BUG},
        {PokeType.PSYCHIC},
    ),
    PokeType.DRAGON: PokeTypeTraits(
        {PokeType.FIRE, PokeType.WATER, PokeType.GRASS, PokeType.ELECTRIC},
        {PokeType.DRAGON, PokeType.ICE, PokeType.FAIRY},
        PokeType.NONE,
    ),
    PokeType.ELECTRIC: PokeTypeTraits(
        {PokeType.FLYING, PokeType.STEEL, PokeType.ELECTRIC},
        {PokeType.GROUND},
        PokeType.NONE,
    ),
    PokeType.FAIRY: PokeTypeTraits(
        {PokeType.FIGHTING, PokeType.BUG, PokeType.DARK},
        {PokeType.POISON, PokeType.STEEL},
        {PokeType.DRAGON},
    ),
    PokeType.FIGHTING: PokeTypeTraits(
        {PokeType.ROCK, PokeType.BUG, PokeType.DARK},
        {PokeType.FLYING, PokeType.PSYCHIC, PokeType.FAIRY},
        PokeType.NONE,
    ),
    PokeType.FIRE: PokeTypeTraits(
        {
            PokeType.BUG,
            PokeType.STEEL,
            PokeType.FIRE,
            PokeType.GRASS,
            PokeType.ICE,
            PokeType.FAIRY,
        },
        {PokeType.GROUND, PokeType.ROCK, PokeType.WATER},
        PokeType.NONE,
    ),
    PokeType.FLYING: PokeTypeTraits(
        {PokeType.FIGHTING, PokeType.BUG, PokeType.GRASS},
        {PokeType.ROCK, PokeType.ELECTRIC, PokeType.ICE},
        {PokeType.GROUND},
    ),
    PokeType.GHOST: PokeTypeTraits(
        {PokeType.POISON, PokeType.BUG},
        {PokeType.GHOST, PokeType.DARK},
        {PokeType.NORMAL, PokeType.FIGHTING},
    ),
    PokeType.GRASS: PokeTypeTraits(
        {PokeType.GROUND, PokeType.WATER, PokeType.GRASS, PokeType.ELECTRIC},
        {PokeType.FLYING, PokeType.POISON, PokeType.BUG, PokeType.FIRE, PokeType.ICE},
        PokeType.NONE,
    ),
    PokeType.GROUND: PokeTypeTraits(
        {PokeType.POISON, PokeType.ROCK},
        {PokeType.WATER, PokeType.GRASS, PokeType.ICE},
        {PokeType.ELECTRIC},
    ),
    PokeType.ICE: PokeTypeTraits(
        {PokeType.ICE},
        {PokeType.FIGHTING, PokeType.FIRE, PokeType.STEEL, PokeType.ROCK},
        PokeType.NONE,
    ),
    PokeType.NORMAL: PokeTypeTraits(
        PokeType.NONE, {PokeType.FIGHTING}, {PokeType.GHOST}
    ),
    PokeType.POISON: PokeTypeTraits(
        {
            PokeType.FIGHTING,
            PokeType.POISON,
            PokeType.BUG,
            PokeType.FAIRY,
            PokeType.GRASS,
        },
        {PokeType.GROUND, PokeType.PSYCHIC},
        PokeType.NONE,
    ),
    PokeType.PSYCHIC: PokeTypeTraits(
        {PokeType.FIGHTING, PokeType.PSYCHIC},
        {PokeType.BUG, PokeType.GHOST, PokeType.GHOST, PokeType.DARK},
        PokeType.NONE,
    ),
    PokeType.ROCK: PokeTypeTraits(
        {PokeType.NORMAL, PokeType.FLYING, PokeType.POISON, PokeType.FIRE},
        {
            PokeType.FIGHTING,
            PokeType.GROUND,
            PokeType.STEEL,
            PokeType.WATER,
            PokeType.GRASS,
        },
        PokeType.NONE,
    ),
    PokeType.STEEL: PokeTypeTraits(
        {
            PokeType.NORMAL,
            PokeType.FLYING,
            PokeType.ROCK,
            PokeType.BUG,
            PokeType.STEEL,
            PokeType.GRASS,
            PokeType.PSYCHIC,
            PokeType.ICE,
            PokeType.DRAGON,
            PokeType.FAIRY,
        },
        {PokeType.FIGHTING, PokeType.GROUND, PokeType.FIRE},
        {PokeType.POISON},
    ),
    PokeType.WATER: PokeTypeTraits(
        {PokeType.STEEL, PokeType.FIRE, PokeType.WATER, PokeType.ICE},
        {PokeType.GRASS, PokeType.ELECTRIC},
        PokeType.NONE,
    ),
}
