from dataclasses import dataclass
from enum import Enum, Flag, auto
from typing import Any, List

from pypogo.pokemon import PvpPokemon


class AILevel(Enum):
    NOVICE = 0
    RIVAL = 1
    ELITE = 2
    CHAMPION = 3


class Strategy(Flag):
    DEFAULT = auto()
    SHIELD = auto()
    SWITCH_BASIC = auto()
    SWITCH_FARM = auto()
    SWITCH_ADVANCED = auto()
    FARM_ENERGY = auto()
    OVERFARM = auto()
    BAIT_SHIELDS = auto()
    WAIT_CLOCK = auto()
    PRESERVE_SWITCH_ADVANTAGE = auto()
    ADVANCED_SHIELDING = auto()
    BAD_DECISION_PROTECTION = auto()
    SACRIFICIAL_SWAP = auto()
    OPTIMIZE_TIMING = auto()


class ScenarioType(Enum):
    BOTH_BAIT = auto()
    NEITHER_BAIT = auto()
    NO_BAIT = auto()
    FARM = auto()


class DecisionType(Enum):
    BASIC = 0
    BEST = 1
    COUNTER = 2
    UNBALANCED = 3
    SAME_TEAM = 4
    SAME_TEAM_DIFFERENT_LEAD = 5
    COUNTER_LAST_LEAD = 6
    PRESET = 7


# Strategies that mean "we are trying to switch out". Strategy is a Flag, so
# membership has to be tested with & rather than by looking inside .value.
SWITCH_STRATEGIES = (
    Strategy.SWITCH_BASIC | Strategy.SWITCH_FARM | Strategy.SWITCH_ADVANCED
)


@dataclass
class Scenario:
    name: ScenarioType
    opponent: PvpPokemon
    matchups: List[int]
    # A shield-weighted mean, so float rather than int.
    average: float
    min_shields: int

    @property
    def rating(self) -> int:
        """
        The single number callers use to ask "how good is this matchup?".

        It is the shield-weighted average battle rating (0-1000) produced by
        `RosterAnalyzer.run_scenario`, exposed under the name the decision
        heuristics use.
        """
        return int(self.average)


@dataclass
class RosterPerformance:
    pokemon: PvpPokemon
    scenarios: List[Scenario]
    average: float


@dataclass
class DecisionOption:
    # Deliberately Any: choose_option is reused for weighted picks over
    # DecisionTypes (team selection), ints (switch target index) and bools
    # (shield yes/no).
    value: Any
    weight: int


@dataclass
class AIArchetype:
    name: str
    level: int
    charged_move_count: int
    iv_combo_range: int
    energy_guess_range: int
    reaction_time: int
    move_guess_certainty: int
    strategies: List[Strategy]


# AI Archetypes as Python list of PvpokeAIRules instances
AI_ARCHETYPES = {
    AILevel.NOVICE: AIArchetype(
        name="Novice",
        level=0,
        charged_move_count=1,
        iv_combo_range=3000,
        energy_guess_range=15,
        reaction_time=12,
        move_guess_certainty=1,
        strategies=[Strategy.DEFAULT, Strategy.SHIELD],
    ),
    AILevel.RIVAL: AIArchetype(
        name="Rival",
        level=1,
        charged_move_count=2,
        iv_combo_range=2000,
        energy_guess_range=10,
        reaction_time=8,
        move_guess_certainty=2,
        strategies=[
            Strategy.DEFAULT,
            Strategy.SHIELD,
            Strategy.SWITCH_BASIC,
        ],
    ),
    AILevel.ELITE: AIArchetype(
        name="Elite",
        level=2,
        charged_move_count=2,
        iv_combo_range=1000,
        energy_guess_range=5,
        reaction_time=4,
        move_guess_certainty=3,
        strategies=[
            Strategy.DEFAULT,
            Strategy.SHIELD,
            Strategy.SWITCH_BASIC,
            Strategy.FARM_ENERGY,
            Strategy.BAIT_SHIELDS,
        ],
    ),
    AILevel.CHAMPION: AIArchetype(
        name="Champion",
        level=3,
        charged_move_count=2,
        iv_combo_range=200,
        energy_guess_range=0,
        reaction_time=0,
        move_guess_certainty=4,
        strategies=[
            Strategy.DEFAULT,
            Strategy.SHIELD,
            Strategy.SWITCH_BASIC,
            Strategy.SWITCH_FARM,
            Strategy.SWITCH_ADVANCED,
            Strategy.FARM_ENERGY,
            Strategy.OVERFARM,
            Strategy.BAIT_SHIELDS,
            Strategy.WAIT_CLOCK,
            Strategy.OPTIMIZE_TIMING,
            Strategy.PRESERVE_SWITCH_ADVANTAGE,
            Strategy.ADVANCED_SHIELDING,
            Strategy.BAD_DECISION_PROTECTION,
            Strategy.SACRIFICIAL_SWAP,
        ],
    ),
}


# Set scenario-specific properties
SCENARIO_TYPES = {
    ScenarioType.BOTH_BAIT: (1, False),  # (min_shields, is_bait)
    ScenarioType.NEITHER_BAIT: (0, False),
    ScenarioType.NO_BAIT: (0, False),
    ScenarioType.FARM: (1, True),
}
