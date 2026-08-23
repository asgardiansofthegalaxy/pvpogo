import pprint

from pypogo.battle import BattlePhase, PvpBattle
from pypogo.player import Player
from pypogo.tests.utils import load_teams

if __name__ == "__main__":
    print("Loading teams...")
    team1, team2 = load_teams()
    player_one = Player(team=team1)
    player_two = Player(team=team2)
    battle = PvpBattle(player_one=player_one, player_two=player_two)

    print("Starting battle...")
    battle.phase = BattlePhase.COUNTDOWN
    battle.simulate()
    print("Battle over!")

    history = battle.get_history()
    print("Battle history:")
    pprint.pprint(history)

    with open("pypogo/scripts/battle_history.txt", "w") as f:
        f.write(pprint.pformat(history, sort_dicts=False))

    print("Player one won!" if battle.is_player_one_winner() else "Player two won!")
