import pprint
from itertools import combinations
from typing import Dict, List, Tuple

from pypogo.battle import BattlePhase, PvpBattle
from pypogo.player import Player
from pypogo.pokemon import PvpPokemon
from pypogo.tests.utils import load_simulation_pokemon

if __name__ == "__main__":
    print("Loading teams...")
    pokemon = load_simulation_pokemon()

    # Generating all unique teams of 3 players each from the 6 players
    all_pokemon_teams : List[Tuple[PvpPokemon, ...]] = list(combinations(pokemon, 3))

    all_players : Dict = {}

    for index, team in enumerate(all_pokemon_teams):
        all_players[index] = Player(team=[pokemon.clone() for pokemon in team], name=index)

    player_records : Dict = {}

    for _index, player in all_players.items():
        player_records[player.name] = {
            "pokemon": player.team,
            "matchups": 0,
            "wins": 0,
            "losses": 0
        }

    # Generate all possible unique matchups for all teams
    all_matchups : List[Tuple] = list(combinations(range(len(all_players)), 2))

    for matchup in all_matchups:
        player1, player2 = matchup
        player_one = all_players[player1]
        player_two = all_players[player2]
    
        battle = PvpBattle(player_one=player_one, player_two=player_two)

        battle.phase = BattlePhase.COUNTDOWN

        battle.simulate()

        player_one.reset_team()
        player_two.reset_team()
        
        player_records[player_one.name]["matchups"] += 1
        player_records[player_two.name]["matchups"] += 1

        if battle.is_player_one_winner():
            player_records[player_one.name]["wins"] += 1
            player_records[player_two.name]["losses"] += 1
        else:
            player_records[player_two.name]["wins"] += 1
            player_records[player_one.name]["losses"] += 1

        history = battle.get_history()
        print("Battle history:")
        pprint.pprint(history)

        print("Player Records:")
        pprint.pprint(player_records)

        with open("pypogo/scripts/simulation_battle_history.txt", "w") as f:
            f.write(pprint.pformat(history, sort_dicts=False))
        
        with open("pypogo/scripts/simulation_player_records.txt", "w") as f:
            f.write(pprint.pformat(player_records, sort_dicts=False))
