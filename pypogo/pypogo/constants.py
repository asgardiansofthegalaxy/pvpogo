from dataclasses import dataclass
from enum import Enum


# Leagues
class League(Enum):
    GREAT_LEAGUE = 1500
    ULTRA_LEAGUE = 2500
    MASTER_LEAGUE = 10000


# Levels
MAX_LEVEL: int = 50  # MAX Pokemon level
MAX_IV: int = 15

# Damage
WEAK_DMG_MOD: float = 1.6
RESIST_DMG_MOD: float = 0.625
IMMUNE_DMG_MOD: float = RESIST_DMG_MOD * RESIST_DMG_MOD
STAB_DMG_MOD: float = 1.2

# Stats
MAX_STAT = 999

BUFF_MULTIPLIER = [
    # Debuff
    0.50000,
    0.57143,
    0.66667,
    0.80000,
    # Baseline
    1.00000,
    # Buff
    1.25000,
    1.50000,
    1.75000,
    2.00000,
]

# CP modifiers at each level
CP_MULTIPLIER = [
    0.0939999967813491,
    0.135137430784308,
    0.166397869586944,
    0.192650914456886,
    0.215732470154762,
    0.236572655026622,
    0.255720049142837,
    0.273530381100769,
    0.290249884128570,
    0.306057381335773,
    0.321087598800659,
    0.335445032295077,
    0.349212676286697,
    0.362457748778790,
    0.375235587358474,
    0.387592411085168,
    0.399567276239395,
    0.411193549517250,
    0.422500014305114,
    0.432926413410414,
    0.443107545375824,
    0.453059953871985,
    0.462798386812210,
    0.472336077786704,
    0.481684952974319,
    0.490855810259008,
    0.499858438968658,
    0.508701756943992,
    0.517393946647644,
    0.525942508771329,
    0.534354329109191,
    0.542635762230353,
    0.550792694091796,
    0.558830599438087,
    0.566754519939422,
    0.574569148039264,
    0.582278907299041,
    0.589887911977272,
    0.597400009632110,
    0.604823657502073,
    0.612157285213470,
    0.619404110566050,
    0.626567125320434,
    0.633649181622743,
    0.640652954578399,
    0.647580963301656,
    0.654435634613037,
    0.661219263506722,
    0.667934000492096,
    0.674581899290818,
    0.681164920330047,
    0.687684905887771,
    0.694143652915954,
    0.700542893277978,
    0.706884205341339,
    0.713169102333341,
    0.719399094581604,
    0.725575616972598,
    0.731700003147125,
    0.734741011137376,
    0.737769484519958,
    0.740785574597326,
    0.743789434432983,
    0.746781208702482,
    0.749761044979095,
    0.752729105305821,
    0.755685508251190,
    0.758630366519684,
    0.761563837528228,
    0.764486065255226,
    0.767397165298461,
    0.770297273971590,
    0.773186504840850,
    0.776064945942412,
    0.778932750225067,
    0.781790064808426,
    0.784636974334716,
    0.787473583646825,
    0.790300011634826,
    0.792803950958807,
    0.795300006866455,
    0.797803921486970,
    0.800300002098083,
    0.802803892322847,
    0.805299997329711,
    0.807803863460723,
    0.810299992561340,
    0.812803834895026,
    0.815299987792968,
    0.817803806620319,
    0.820299983024597,
    0.822803778631297,
    0.825299978256225,
    0.827803750922782,
    0.830299973487854,
    0.832803753381377,
    0.835300028324127,
    0.837803755931569,
    0.840300023555755,
    0.842803729034748,
    0.845300018787384,
    0.847803702398935,
    0.850300014019012,
    0.852803676019539,
    0.855300009250640,
    0.857803649892077,
    0.860300004482269,
    0.862803624012168,
    0.865299999713897,
]


# Battle


# Simulated battles only support `NEUTRAL', `SUSPEND_CHARGED', and
# `SUSPEND_SWITCH_TIE' phases.
class BattlePhase(Enum):
    COUNTDOWN = 0
    NEUTRAL = 1
    SUSPEND_CHARGED = 2
    SUSPEND_CHARGED_ATTACK = 3
    SUSPEND_CHARGED_SHIELD = 4
    SUSPEND_CHARGED_NO_SHIELD = 5
    SUSPEND_SWITCH_P1 = 6
    SUSPEND_SWITCH_P2 = 7
    SUSPEND_SWITCH_TIE = 8
    GAME_OVER = 9

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, BattlePhase):
            return NotImplemented
        return self.value == __value.value

    def __hash__(self) -> int:
        # Defining __eq__ sets __hash__ to None, which would make members
        # unusable as dict keys or set elements.
        return hash(self.value)


# Bonus Multipliers
PVP_FAST_BONUS_MOD = 1.3
PVP_CHARGE_BONUS_MOD = 1.3

# Charged Move Score Modifiers
CHARGE_BASE_MOD = 0.25
CHARGE_NICE_MOD = 0.5
CHARGE_GREAT_MOD = 0.75
CHARGE_EXCELLENT_MOD = 1.0
CHARGE_DEFAULT_MOD = CHARGE_EXCELLENT_MOD  # Assumes players hit "Excellent" in all Charged Move Minigames

# Other Multipliers and Constants
STAB_BONUS = 1.25
SHADOW_ATTACK_MOD = 1.2
SHADOW_DEFENSE_MOD = 0.8333333
MAX_CHARGE = 100  # Energy cap
CHARGE_RATE = 20
CHARGE_DECAY_RATE = 0.5

STARTING_SHIELDS = 2


# Utility Functions
def mins_secs_to_ms(mins, secs):
    return (mins * 60 + secs) * 1000


# Time-related Constants (in milliseconds)
BATTLE_TIME = mins_secs_to_ms(4.5, 0)
TURN_TIME = mins_secs_to_ms(0, 0.5)
CHARGED_ANIM_TIME = mins_secs_to_ms(0, 4)
CHARGED_MG_TIME = mins_secs_to_ms(0, 10)
CHARGED_TIME = CHARGED_ANIM_TIME + CHARGED_MG_TIME
SWITCH_ANIM_TIME = mins_secs_to_ms(0, 1)
SWITCH_TIMEOUT = mins_secs_to_ms(0, 12)
SWITCH_TIME = SWITCH_ANIM_TIME + SWITCH_TIMEOUT

# Time-related Constants (in turns)
BATTLE_TURNS = BATTLE_TIME / TURN_TIME
CHARGED_ANIM_TURNS = CHARGED_ANIM_TIME / TURN_TIME
CHARGED_MG_TURNS = CHARGED_MG_TIME / TURN_TIME
CHARGED_TURNS = CHARGED_TIME / TURN_TIME
SWITCH_ANIM_TURNS = SWITCH_ANIM_TIME / TURN_TIME
SWITCH_TIMEOUT_TURNS = SWITCH_TIMEOUT / TURN_TIME
SWITCH_TURNS = SWITCH_TIME / TURN_TIME


class BattleMode(Enum):
    SIMULATE = 0
    EMULATE = 1


class BattleEndCond(Enum):
    FIRST_FAINT = 0
    BOTH_FAINT = 1


#: Seed for a battle's charge-move-priority coin flip. A fixed default makes
#: every simulation reproducible, which is what lets analysis results be
#: precomputed and checked for drift. Pass cmp_seed=None to PvpBattle for the
#: live game's genuine unpredictability.
DEFAULT_CMP_SEED = 0

#: Default seed for a battle AI's own RNG. `PvPokeAI` weighs several decisions
#: by chance -- which shield call to make, whether to overfarm, how far off its
#: guess at the opponent's energy is -- and drawing those from the global RNG
#: made its results unreproducible, exactly as the charge-move tie above once
#: was. Pass `seed=None` to opt back into genuine unpredictability.
DEFAULT_AI_SEED = 0


class CMPRule(Enum):
    CMP_IDEAL = 0
    CMP_ALTERNATE = 1
    CMP_FAVOR_P1 = 2
    CMP_FAVOR_P2 = 3


# PvP Pokemon Log Structure
@dataclass
class PvpPokemonLog:
    total_damage: int
    total_charged_damage: int
    total_damage_blocked: int
    total_energy_gained: int
    total_energy_used: int
    damage_against_shields: int
    damage_through_shields: int
    shields_used: int
    shields_hit: int
    switch_advantages: int
