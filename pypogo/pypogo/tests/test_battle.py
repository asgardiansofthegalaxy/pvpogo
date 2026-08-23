from unittest import TestCase, mock
from pypogo.battle import PvpBattle, BattlePhase, PvpAction
from pypogo.moves import MoveKind
from pypogo.player import Player
from .utils import load_teams


class PvpBattleTests(TestCase):
    def setUp(self) -> None:
        team1, team2 = load_teams()
        self.p1 = Player(team=team1)
        self.p2 = Player(team=team2)
        self.battle = PvpBattle(player_one=self.p1, player_two=self.p2)

    def test_simulate_battle(self):
        # When
        turns = self.battle.simulate()

        # Then
        self.assertEqual(self.battle.phase, BattlePhase.GAME_OVER)
        self.assertGreater(turns, 0)

    def test_simulate_1v1_matches_pvpoke(self):
        # Given
        self.p1.team = [self.p1.team[0]]
        self.p2.team = [self.p2.team[0]]
        self.p1._shields = 0
        self.p2._shields = 0
        self.assertEqual(self.p1.active_pokemon.pdex_mon.species_name, "Azumarill")
        self.assertEqual(self.p2.active_pokemon.pdex_mon.species_name, "Skarmory")

        # When
        turns = self.battle.simulate()

        # Then
        self.assertEqual(self.battle.phase, BattlePhase.GAME_OVER)
        self.assertFalse(self.battle.is_player_one_winner())
        self.assertEqual(turns, 32)

        # Verify stats
        self.assertEqual(self.p1.active_pokemon.hp, 0)
        self.assertEqual(self.p2.active_pokemon.hp, 19)

    def test_is_battle_over(self):
        # Set the battle phase to GAME_OVER
        self.battle.phase = BattlePhase.GAME_OVER

        # Assert that is_battle_over returns True
        self.assertTrue(self.battle.is_battle_over())

        # Set the battle phase to NEUTRAL
        self.battle.phase = BattlePhase.NEUTRAL

        # Assert that is_battle_over returns False
        self.assertFalse(self.battle.is_battle_over())

        # Set the remaining pokemon count to 0 for player one
        self.p1.get_remaining_pokemon = mock.Mock(return_value=0)

        # Assert that is_battle_over returns True
        self.assertTrue(self.battle.is_battle_over())

        # Set the remaining pokemon count to 1 for player one and two
        self.p1.get_remaining_pokemon = mock.Mock(return_value=1)
        self.p2.get_remaining_pokemon = mock.Mock(return_value=1)

        # Assert that is_battle_over returns False
        self.assertFalse(self.battle.is_battle_over())

    def test_is_player_one_winner(self):
        # Set the battle phase to GAME_OVER
        self.battle.phase = BattlePhase.GAME_OVER

        # Set the remaining pokemon count to 0 for player two
        self.p2.get_remaining_pokemon = mock.Mock(return_value=0)

        # Assert that is_player_one_winner returns True
        self.assertTrue(self.battle.is_player_one_winner())

        # Set the remaining pokemon count to 1 for player one
        self.p2.get_remaining_pokemon = mock.Mock(return_value=1)
        self.p1.get_remaining_pokemon = mock.Mock(return_value=0)

        # Assert that is_player_one_winner returns False
        self.assertFalse(self.battle.is_player_one_winner())

    def test_get_battle_winner(self):
        # Set the battle phase to GAME_OVER
        self.battle.phase = BattlePhase.GAME_OVER

        # Set the remaining pokemon count to 0 for both players
        self.p1.get_remaining_pokemon = mock.Mock(return_value=0)
        self.p2.get_remaining_pokemon = mock.Mock(return_value=0)

        # Assert that get_battle_winner returns None
        self.assertIsNone(self.battle.get_battle_winner())

        # Set the remaining pokemon count to 1 for player one
        self.p1.get_remaining_pokemon = mock.Mock(return_value=1)

        # Assert that get_battle_winner returns player one
        self.assertEqual(self.battle.get_battle_winner(), self.p1)

        # Set the remaining pokemon count to 1 for player two
        self.p1.get_remaining_pokemon = mock.Mock(return_value=0)
        self.p2.get_remaining_pokemon = mock.Mock(return_value=1)

        # Assert that get_battle_winner returns player two
        self.assertEqual(self.battle.get_battle_winner(), self.p2)

    def test_eval_turn(self):
        # Set the player actions to FAST
        self.battle.p1_action = PvpAction.FAST
        self.battle.p2_action = PvpAction.FAST

        # Set the battle phase to NEUTRAL
        self.battle.phase = BattlePhase.NEUTRAL

        self.assertTrue(self.p1.is_active_alive)
        self.assertTrue(self.p2.is_active_alive)

        # Call the _eval_turn method
        result = self.battle._eval_turn()

        # Assert that the result is False
        self.assertFalse(result)

        # Set the player actions to WAIT
        self.battle.p1_action = PvpAction.WAIT
        self.battle.p2_action = PvpAction.WAIT

        # Call the _eval_turn method
        result = self.battle._eval_turn()

        # Assert that the result is False
        self.assertFalse(result)

    def test_eval_turn_simulated(self):
        # Given battle is ongoing
        self.battle.phase = BattlePhase.NEUTRAL
        self.battle.p1_action = PvpAction.FAST
        self.battle.p2_action = PvpAction.FAST

        # Evaluate turn
        is_battle_over = self.battle._eval_turn_simulated()

        # Assert that the battle isn't over
        self.assertFalse(is_battle_over)

        # Given all pokemon of player one have fainted and player two has no cooldown
        self.p1.get_remaining_pokemon = mock.Mock(return_value=0)
        self.p2.get_cooldown = mock.Mock(return_value=0)
        self.battle.p2_action = PvpAction.FAST

        # Call the _eval_turn_simulated method
        is_battle_over = self.battle._eval_turn_simulated()

        # Assert that the battle is over
        self.assertTrue(is_battle_over)

    def test_process_suspend_switch_tie_phase_actions(self):
        # Set the player actions to SWITCH1
        self.battle.p1_action = PvpAction.SWITCH1
        self.battle.p2_action = PvpAction.SWITCH1

        # Mock the do_switch method of the players
        self.p1.do_switch = mock.Mock()
        self.p2.do_switch = mock.Mock()

        # Call the _process_suspend_switch_tie_phase_actions method
        self.battle._process_suspend_switch_tie_phase_actions(
            self.battle.p1_action, self.battle.p2_action
        )

        # Assert that the do_switch method is called for both players
        self.p1.do_switch.assert_called_with(True)
        self.p2.do_switch.assert_called_with(True)

    def test_do_fast(self):
        # Given
        original_hp = self.p2.active_pokemon.hp
        self.p2.active_pokemon.fast_move._turns = 2  # Set the cooldown to 2
        self.p2.active_pokemon.fast_move.energy = 10

        damage = 10
        self.p1.active_pokemon.calculate_damage = mock.Mock(return_value=damage)

        # When
        self.battle.p1.do_fast(defender=self.p2)

        # Then
        # Defender's hp goes down by amount of damage
        self.assertEqual(
            self.p2.active_pokemon.hp,
            original_hp - damage,
        )
        # Attacker's cooldown increases by the move's cooldown
        self.assertEqual(
            self.p1.active_pokemon.cooldown_turns,
            self.p1.active_pokemon.fast_move.cooldown_turns,
        )
        # Attacker's energy increases by the move's energy
        self.assertEqual(
            self.p1.active_pokemon.energy,
            self.p1.active_pokemon.fast_move.energy_gain,
        )

    def test_do_charged(self):
        # Given
        self.p1.active_pokemon.energy = 150
        original_hp = self.p2.active_pokemon.hp
        self.p1.active_pokemon.charged_moves[0].energy = 100
        self.p2._shields = 0
        self.p2.decide_action = mock.Mock(return_value=PvpAction.WAIT)

        damage = 50
        self.p1.active_pokemon.calculate_damage = mock.Mock(return_value=damage)

        # When
        self.battle._do_charged(
            attacker=self.p1,
            defender=self.p2,
            action=PvpAction.CHARGED1,
        )

        # Defender's pokemon hp goes down by amount of damage
        self.assertEqual(
            self.p2.active_pokemon.hp,
            original_hp - damage,
        )

        # Attacker's energy goes down by move's energy
        self.assertEqual(
            self.p1.active_pokemon.energy,
            150 - self.p1.active_pokemon.charged_moves[0].energy,
        )
