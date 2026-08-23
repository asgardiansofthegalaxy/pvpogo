from enum import Enum

from pypogo.moves import MoveKind


class PvpAction(Enum):
    ACT_NULL = 0
    FAST = 1
    WAIT = 2
    CHARGED1 = 3
    CHARGED2 = 4
    SWITCH1 = 5
    SWITCH2 = 6
    SHIELD = 7

    @property
    def is_charged(self):
        return self in (PvpAction.CHARGED1, PvpAction.CHARGED2)

    @property
    def is_fast(self):
        return self == PvpAction.FAST

    @property
    def is_attack(self):
        return self == PvpAction.FAST or self.is_charged

    @property
    def is_switch(self):
        return self in (PvpAction.SWITCH1, PvpAction.SWITCH2)

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, PvpAction):
            return NotImplemented
        return self.value == __value.value

    def __hash__(self) -> int:
        # Defining __eq__ sets __hash__ to None, which would make members
        # unusable as dict keys or set elements.
        return hash(self.value)

    @property
    def move_kind(self):
        if self.is_fast:
            return MoveKind.FAST
        elif self == PvpAction.CHARGED1:
            return MoveKind.CHARGED1
        elif self == PvpAction.CHARGED2:
            return MoveKind.CHARGED2
        else:
            raise RuntimeError(f"Action {self} is not a valid move type")
