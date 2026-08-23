from pypogo.ai.interface import AInterface, AIStatus
from pypogo.action import PvpAction


class NaiveAI(AInterface):
    def __init__(self, player, name="NaiveAI"):
        self.player = player
        self.name = name

    def select_team(
        self,
        previous_teams=None,
        previous_result: str = None,
        selection_strategy=None,
    ):
        return AIStatus.AI_ERROR_FAIL

    def decide_action(self, battle_phase):
        eligible_actions = [
            PvpAction.CHARGED1,
            PvpAction.CHARGED2,
            PvpAction.SHIELD,
            PvpAction.FAST,
            PvpAction.WAIT,
            PvpAction.SWITCH1,
        ]

        for eligible_action in eligible_actions:
            if self.is_valid_action(eligible_action, battle_phase):
                action = eligible_action
                break
        else:
            action = PvpAction.ACT_NULL

        result = (
            AIStatus.AI_SUCCESS
            if action != PvpAction.ACT_NULL
            else AIStatus.AI_ERROR_FAIL
        )
        return result, action

    def decide_switch(self):
        return AIStatus.AI_ERROR_FAIL

    def decide_shield(self):
        return AIStatus.AI_ERROR_FAIL
