from typing import List
from pypogo.game_master.game_master import GameMaster
from pypogo.pokemon import Pokemon

GM = GameMaster()


def load_all_grass_team() -> List[Pokemon]:
    grass_pokemon = [
        {
            "species_id": "snivy",
            "fast_move_id": "VINE_WHIP",
            "charged_move_ids": ["ENERGY_BALL", "SEED_BOMB"],
        },
        {
            "species_id": "chikorita",
            "fast_move_id": "VINE_WHIP",
            "charged_move_ids": ["GRASS_KNOT", "ENERGY_BALL"],
        },
        {
            "species_id": "treecko",
            "fast_move_id": "BULLET_SEED",
            "charged_move_ids": ["ENERGY_BALL", "GRASS_KNOT"],
        },
    ]
    team = [GM.get_pokemon(**data) for data in grass_pokemon]
    return team


def load_all_fire_team() -> List[Pokemon]:
    fire_pokemon = [
        {
            "species_id": "charmander",
            "fast_move_id": "EMBER",
            "charged_move_ids": ["FLAME_CHARGE", "FLAMETHROWER"],
        },
        {
            "species_id": "cyndaquil",
            "fast_move_id": "EMBER",
            "charged_move_ids": ["FLAMETHROWER", "FLAME_CHARGE"],
        },
        {
            "species_id": "torchic",
            "fast_move_id": "EMBER",
            "charged_move_ids": ["FLAME_CHARGE", "FLAMETHROWER"],
        },
    ]
    team = [GM.get_pokemon(**data) for data in fire_pokemon]
    return team


def load_all_water_team() -> List[Pokemon]:
    water_pokemon = [
        {
            "species_id": "squirtle",
            "fast_move_id": "BUBBLE",
            "charged_move_ids": ["AQUA_JET", "WATER_PULSE"],
        },
        {
            "species_id": "totodile",
            "fast_move_id": "WATER_GUN",
            "charged_move_ids": ["WATER_PULSE", "AQUA_JET"],
        },
        {
            "species_id": "froakie",
            "fast_move_id": "BUBBLE",
            "charged_move_ids": ["WATER_PULSE", "SURF"],
        },
    ]
    team = [GM.get_pokemon(**data) for data in water_pokemon]
    return team
