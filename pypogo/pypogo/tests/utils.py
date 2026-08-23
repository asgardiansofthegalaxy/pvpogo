import json

from pypogo.game_master.game_master import GameMaster
from pypogo.moves import Move
from pypogo.pokedex import PokedexEntry
from pypogo.pokemon import Pokemon, PvpPokemon
from pypogo.stats import Stats

GM = GameMaster()


def load_bulbasaur_data():
    with open("pypogo/tests/fixtures/bulbasaur.json", "r") as file:
        return json.load(file)


def load_bulbasaur_moves():
    with open("pypogo/tests/fixtures/bulbasaur_attacks.json", "r") as file:
        return json.load(file)


def load_bulbasaur() -> Pokemon:
    bulbasaur_data = load_bulbasaur_data()
    bulbasaur = PokedexEntry.from_dict(bulbasaur_data)
    moves_data = load_bulbasaur_moves()
    fast_move = Move.from_dict(moves_data["fast"])
    charge_moves = [Move.from_dict(move) for move in moves_data["charged"]]

    return Pokemon(
        pdex_mon=bulbasaur,
        level=50.0,
        ivs=Stats(attack=15, defense=15, stamina=15),
        fast_move=fast_move,
        charged_moves=charge_moves,
    )


def load_team():
    team1, _ = load_teams()
    return team1


def load_wrap():
    with open("pypogo/tests/fixtures/wrap.json", "r") as file:
        return json.load(file)


def load_teams():
    """
    teams_data = {
        'team1': {
            'azumarill': {'fast': 'BUBBLE', 'charged': ['ICE_BEAM', 'PLAY_ROUGH'], 'level': 45.5, 'stats': Stats(0, 15, 15)},
            'serperior': {'fast': 'VINE_WHIP', 'charged': ['FRENZY_PLANT', 'AERIAL_ACE'], 'level': 25.5, 'stats': Stats(0, 10, 15)},
            'talonflame': {'fast': 'INCINERATE', 'charged': ['FLY', 'FLAME_CHARGE'], 'level': 26, 'stats': Stats(0, 13, 15)}
        },
        'team2': {
            'skarmory': {'fast': 'STEEL_WING', 'charged': ['BRAVE_BIRD', 'SKY_ATTACK'], 'level': 27.5, 'stats': Stats(0, 15, 14)},
            'stunfisk_galarian': {'fast': 'MUD_SHOT', 'charged': ['ROCK_SLIDE', 'EARTHQUAKE'], 'level': 27, 'stats': Stats(0, 12, 15)},
            'medicham': {'fast': 'COUNTER', 'charged': ['ICE_PUNCH', 'DYNAMIC_PUNCH'], 'level': 50, 'stats': Stats(5, 15, 15)}
        }}
    """
    with open("pypogo/tests/fixtures/teams.json", "r") as file:
        teams_data = json.load(file)
    team1 = [PvpPokemon.from_dict(td) for td in teams_data["team1"]]
    team2 = [PvpPokemon.from_dict(td) for td in teams_data["team2"]]
    return team1, team2


def load_simulation_pokemon():
    with open("pypogo/tests/fixtures/simulation_pokemon.json", "r") as file:
        pokemon = json.load(file)
    pokemon = [GM.get_pokemon(**data) for data in pokemon]

    return pokemon
