from unittest import TestCase

from pypogo.buff import BuffLevel, BuffState


class BuffStateTests(TestCase):
    def setUp(self) -> None:
        self.buff_state = BuffState()

    def test_debuff_attack(self):
        self.assertEqual(self.buff_state.debuff_attack(2), BuffLevel.B_4_6)
        self.assertEqual(self.buff_state.debuff_attack(4), BuffLevel.B_4_8)
        self.assertEqual(self.buff_state.debuff_attack(6), BuffLevel.B_4_8)

    def test_debuff_defense(self):
        self.assertEqual(self.buff_state.debuff_defense(2), BuffLevel.B_4_6)
        self.assertEqual(self.buff_state.debuff_defense(4), BuffLevel.B_4_8)
        self.assertEqual(self.buff_state.debuff_defense(6), BuffLevel.B_4_8)

    def test_buff_attack(self):
        self.assertEqual(self.buff_state.buff_attack(2), BuffLevel.B_6_4)
        self.assertEqual(self.buff_state.buff_attack(4), BuffLevel.B_8_4)
        self.assertEqual(self.buff_state.buff_attack(6), BuffLevel.B_8_4)

    def test_buff_defense(self):
        self.assertEqual(self.buff_state.buff_defense(2), BuffLevel.B_6_4)
        self.assertEqual(self.buff_state.buff_defense(4), BuffLevel.B_8_4)
        self.assertEqual(self.buff_state.buff_defense(6), BuffLevel.B_8_4)

    def test_attack_multiplier(self):
        self.assertEqual(self.buff_state.attack_multiplier, 1.0)

    def test_defense_multiplier(self):
        self.assertEqual(self.buff_state.defense_multiplier, 1.0)
