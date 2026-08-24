from unittest import TestCase

from pypogo.action import PvpAction
from pypogo.ai.interface import AIStatus
from pypogo.ai.pvpoke.constants import AILevel, DecisionType, ScenarioType
from pypogo.ai.pvpoke.pvpoke import PvPokeAI
from pypogo.ai.pvpoke.roster_analysis import RosterAnalyzer
from pypogo.battle import BattlePhase, PvpBattle
from pypogo.player import Player
from pypogo.tests.utils import load_teams


class PvPokeAITests(TestCase):
    def setUp(self):
        team_one, team_two = load_teams()
        self.player = Player(team=team_one, name="pvpoke")
        self.opponent = Player(team=team_two, name="naive")
        self.ai = PvPokeAI(self.player, level=AILevel.CHAMPION)
        self.player.ai = self.ai
        self.battle = PvpBattle(self.player, self.opponent)
        self.battle.phase = BattlePhase.NEUTRAL

    def test_battle_wires_opponent_and_turn(self):
        self.assertIs(self.ai.opponent, self.opponent)
        self.assertEqual(self.ai.turn, self.battle.turn)

    def test_opponent_and_turn_default_outside_a_battle(self):
        loose_player = Player(team=load_teams()[0])
        loose_ai = PvPokeAI(loose_player)

        self.assertIsNone(loose_ai.opponent)
        self.assertEqual(loose_ai.turn, 0)

    def test_decide_action_returns_status_action_pair(self):
        status, action = self.ai.decide_action(BattlePhase.NEUTRAL)

        self.assertEqual(status, AIStatus.AI_SUCCESS)
        self.assertTrue(self.ai.is_valid_action(action, BattlePhase.NEUTRAL))

    def test_decide_action_without_opponent_reports_bad_value(self):
        loose_player = Player(team=load_teams()[0])
        loose_ai = PvPokeAI(loose_player)

        status, action = loose_ai.decide_action(BattlePhase.NEUTRAL)

        self.assertEqual(status, AIStatus.AI_ERROR_BAD_VALUE)
        self.assertEqual(action, PvpAction.ACT_NULL)

    def test_decide_action_answers_a_charged_move_with_shield_or_wait(self):
        status, action = self.ai.decide_action(BattlePhase.SUSPEND_CHARGED)

        self.assertEqual(status, AIStatus.AI_SUCCESS)
        self.assertIn(action, (PvpAction.SHIELD, PvpAction.WAIT))

    def test_decide_action_game_over_fails(self):
        status, action = self.ai.decide_action(BattlePhase.GAME_OVER)

        self.assertEqual(status, AIStatus.AI_ERROR_FAIL)
        self.assertEqual(action, PvpAction.ACT_NULL)

    def test_decide_switch_picks_a_live_benched_pokemon(self):
        target = self.ai.decide_switch()

        self.assertIsNotNone(target)
        self.assertNotEqual(target, self.player._active_pokemon_idx)
        self.assertGreater(self.player.team[target].hp, 0)

    def test_switch_action_maps_to_a_valid_switch(self):
        action = self.ai._switch_action()

        self.assertIn(action, (PvpAction.SWITCH1, PvpAction.SWITCH2))
        self.assertTrue(self.ai.is_valid_action(action, BattlePhase.NEUTRAL))

    def test_decide_switch_returns_none_with_an_empty_bench(self):
        self.player.team = [self.player.active_pokemon]

        self.assertIsNone(self.ai.decide_switch())
        self.assertIsNone(self.ai._switch_action())

    def test_decide_shield_returns_a_bool(self):
        self.assertIsInstance(self.ai.decide_shield(), bool)

    def test_select_team_strategies_each_return_a_team(self):
        for strategy in (
            DecisionType.BASIC,
            DecisionType.BEST,
            DecisionType.COUNTER,
            DecisionType.UNBALANCED,
        ):
            with self.subTest(strategy=strategy):
                team = self.ai.select_team(selection_strategy=strategy)
                self.assertEqual(len(team), 3)

    def test_select_team_falls_back_when_there_is_no_previous_round(self):
        team = self.ai.select_team(selection_strategy=DecisionType.SAME_TEAM)

        self.assertEqual(len(team), 3)

    def test_scenario_cache_avoids_repeated_simulation(self):
        attacker = self.player.active_pokemon
        defender = self.opponent.active_pokemon

        first = self.ai._run_scenario(ScenarioType.NO_BAIT, attacker, defender)
        second = self.ai._run_scenario(ScenarioType.NO_BAIT, attacker, defender)

        self.assertIs(first, second)

    def test_scenario_rating_matches_weighted_average(self):
        scenario = RosterAnalyzer.run_scenario(
            ScenarioType.NO_BAIT,
            self.player.active_pokemon,
            self.opponent.active_pokemon,
        )

        self.assertEqual(scenario.rating, int(scenario.average))


class PvPokeAIBattleTests(TestCase):
    def test_pvpoke_ai_can_drive_a_full_battle_at_every_level(self):
        for level in AILevel:
            with self.subTest(level=level):
                team_one, team_two = load_teams()
                player = Player(team=team_one, name="pvpoke")
                opponent = Player(team=team_two, name="naive")
                player.ai = PvPokeAI(player, level=level)

                battle = PvpBattle(player, opponent)
                battle.phase = BattlePhase.COUNTDOWN
                turns = battle.simulate()

                self.assertGreater(turns, 0)
                self.assertEqual(battle.phase, BattlePhase.GAME_OVER)

                # The point is that the AI drives the battle to a finish, not
                # that it wins: a double KO wipes both teams and is a legal
                # outcome, which `get_battle_winner` reports as a tie. ELITE
                # reaches one on this fixture.
                self.assertEqual(
                    min(
                        player.get_remaining_pokemon(),
                        opponent.get_remaining_pokemon(),
                    ),
                    0,
                    "a finished battle must have wiped at least one team",
                )

    def test_pvpoke_ai_can_battle_another_pvpoke_ai(self):
        team_one, team_two = load_teams()
        player = Player(team=team_one, name="champion")
        opponent = Player(team=team_two, name="novice")
        player.ai = PvPokeAI(player, level=AILevel.CHAMPION)
        opponent.ai = PvPokeAI(opponent, level=AILevel.NOVICE)

        battle = PvpBattle(player, opponent)
        battle.phase = BattlePhase.COUNTDOWN
        turns = battle.simulate()

        self.assertGreater(turns, 0)
        self.assertEqual(battle.phase, BattlePhase.GAME_OVER)
