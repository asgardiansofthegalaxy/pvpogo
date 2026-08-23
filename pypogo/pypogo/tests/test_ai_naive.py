from unittest import TestCase
from pypogo.constants import BattlePhase

from pypogo.player import Player
from pypogo.ai.naive import NaiveAI, AIStatus, PvpAction
from pypogo.tests.utils import load_team


class NaiveAITests(TestCase):
    def setUp(self) -> None:
        self.team = load_team()
        self.player = Player(self.team)
        self.naive_ai = NaiveAI(player=self.player)

    def test_select_team(self):
        result = self.naive_ai.select_team()
        self.assertEqual(result, AIStatus.AI_ERROR_FAIL)

    def test_decide_action_valid_action(self):
        player = None  # Replace with actual player object
        battle_phase = BattlePhase.NEUTRAL  # Replace with actual battle phase
        result, action = self.naive_ai.decide_action(battle_phase)
        self.assertEqual(result, AIStatus.AI_SUCCESS)
        self.assertIn(
            action,
            [
                PvpAction.CHARGED1,
                PvpAction.CHARGED2,
                PvpAction.SHIELD,
                PvpAction.FAST,
                PvpAction.SWITCH1,
                PvpAction.WAIT,
            ],
        )

    def test_decide_action_invalid_action(self):
        battle_phase = BattlePhase.GAME_OVER
        result, action = self.naive_ai.decide_action(battle_phase)
        self.assertEqual(result, AIStatus.AI_ERROR_FAIL)
        self.assertEqual(action, PvpAction.ACT_NULL)

    def test_decide_switch(self):
        result = self.naive_ai.decide_switch()
        self.assertEqual(result, AIStatus.AI_ERROR_FAIL)

    def test_decide_shield(self):
        result = self.naive_ai.decide_shield()
        self.assertEqual(result, AIStatus.AI_ERROR_FAIL)

    def test_is_valid_action_fast_valid(self):
        action = PvpAction.FAST
        battle_phase = BattlePhase.NEUTRAL
        result = self.naive_ai.is_valid_action(action, battle_phase)
        self.assertTrue(result)

    def test_is_valid_action_fast_invalid(self):
        action = PvpAction.FAST
        battle_phase = BattlePhase.SUSPEND_CHARGED
        result = self.naive_ai.is_valid_action(action, battle_phase)
        self.assertFalse(result)
