"""
A single reproducible number for how well a battle AI plays.

The project has four AI tiers, a heuristic port with a known dormant branch,
and no way to tell whether a change to any of it helps. Tuning against a number
you cannot reproduce is not tuning, so this is the prerequisite for touching the
AI at all -- notably for the strategy state machine, whose first naive attempt
made CHAMPION play *worse* than NOVICE and would have looked like an
improvement to anyone eyeballing single battles.

**How the number is anchored.** An AI is scored by playing a fixed suite of
team matchups against a reference AI. Each matchup is played twice, swapping
*both* the team and the seat:

    battle 1:  seat one = AI plays X      seat two = reference plays Y
    battle 2:  seat one = reference plays X   seat two = AI plays Y

and the AI's score is the mean of its rating in each. Because a battle's rating
splits one outcome between its two sides -- `rating(X) + rating(Y) == 1000` --
an AI that plays exactly like the reference produces the same battle twice and
scores exactly 500, whatever the teams were. So:

* **500 means indistinguishable from the reference.**
* The distance from 500 is the margin, in rating points.
* Neither the team sample nor the seat can bias the result: the AI and the
  reference hold each team in each seat exactly once.

Swapping the seat matters. A 3v3 with identical AIs on both sides is not quite
seating-independent -- seat one is worth about 4 rating points -- so an AI that
always sat first would score ~504 against a copy of itself. That is small next
to the ~50-80 points separating the tiers, but it is exactly the sort of
constant offset that makes a benchmark lie about small improvements.

**The suite is 3v3**, because that is the format the AI is written for. In a
1v1 there is nothing to switch to, so `decide_switch` never runs and the tiers
score within a point of each other -- a 1v1 benchmark would report that every
tier is equivalent, which is true only of the half of the AI it exercises.

Teams are drawn from a league's committed meta -- the strongest picks the
project knows of, derived rather than curated -- so it measures play against
the kind of Pokemon an AI actually has to handle.
"""

import json
import os
from dataclasses import dataclass, field
from itertools import combinations
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from pypogo.ai.interface import AInterface
from pypogo.ai.naive import NaiveAI
from pypogo.battle import PvpBattle
from pypogo.game_master.game_master import CWD, GameMaster
from pypogo.meta import Build, instantiate, matchups_filename
from pypogo.player import Player
from pypogo.pokemon import PvpPokemon

#: Builds an AI for a player. `PvPokeAI` needs its level bound, so scoring
#: takes a factory rather than a class.
AiFactory = Callable[[Player], AInterface]

#: The rating an even battle produces, and what an AI scores against itself.
EVEN = 500.0

#: Pokemon per team. Three is a GO Battle League team.
TEAM_SIZE = 3

#: A team pairing: two teams, played twice with the seats swapped.
Pairing = Tuple[Tuple[Build, ...], Tuple[Build, ...]]


def team_rating(team: Sequence[PvpPokemon], opposing: Sequence[PvpPokemon]) -> float:
    """
    How well `team` did: half the damage it dealt, half the HP it kept.

    The team-level form of `OneVsOneBattle._get_battle_rating`, and identical
    to it for a team of one -- `tests/test_fitness.py` pins that. Both sides'
    ratings sum to 1000, which is what anchors a fitness score at 500.
    """
    opposing_hp = sum(m.full_hp for m in opposing)
    own_hp = sum(m.full_hp for m in team)
    dealt = sum(m.full_hp - m.hp for m in opposing) / opposing_hp
    kept = sum(m.hp for m in team) / own_hp
    return EVEN * dealt + EVEN * kept


@dataclass(frozen=True)
class MatchupResult:
    """One team pairing, played from both seats."""

    team_one: Tuple[str, ...]
    team_two: Tuple[str, ...]
    #: The AI's rating playing team one in seat one, then team two in seat two.
    as_one: float
    as_two: float

    @property
    def score(self) -> float:
        """Mean of the two. 500 if the AI played like the reference."""
        return (self.as_one + self.as_two) / 2


@dataclass(frozen=True)
class FitnessReport:
    """What one AI scored, plus enough detail to see where it came from."""

    score: float
    league: str
    battles: int
    results: List[MatchupResult] = field(default_factory=list)

    @property
    def edge(self) -> float:
        """Rating points above the reference. Negative means worse than it."""
        return self.score - EVEN

    def worst(self, limit: int = 5) -> List[MatchupResult]:
        """Where this AI loses the most ground. The first place to look."""
        return sorted(self.results, key=lambda r: r.score)[:limit]

    def best(self, limit: int = 5) -> List[MatchupResult]:
        return sorted(self.results, key=lambda r: -r.score)[:limit]


def league_meta(league: str) -> List[dict]:
    """
    The committed meta for a league, which the suite is drawn from.

    Reading the shipped file rather than re-deriving the meta keeps a fitness
    run seconds instead of minutes, and means the suite is the same set of
    Pokemon the matchup matrix is built on.
    """
    path = os.path.join(CWD, matchups_filename(league))
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing {path}. Build it with:\n"
            f"  cd pypogo && python3 pypogo/scripts/build_matchups.py --league {league}"
        )
    with open(path) as fp:
        return json.load(fp)["meta"]


def build_suite(
    meta: Sequence[dict], teams: int = 4, team_size: int = TEAM_SIZE
) -> List[Pairing]:
    """
    Every pairing among `teams` teams cut from the head of a league's meta.

    The meta is ordered by score, so consecutive chunks of three give teams of
    comparable strength without anyone choosing them -- the same "derived, not
    curated" rule the meta itself follows. Pairings grow quadratically: four
    teams is six pairings, and each pairing is two battles.
    """
    needed = teams * team_size
    if len(meta) < needed:
        raise ValueError(f"meta has {len(meta)} picks; {needed} needed for the suite")

    builds = [
        Build(
            species_id=entry["id"],
            level=entry["level"],
            fast_move=entry["fast"],
            charged_moves=tuple(entry["charged"]),
            cp=entry["cp"],
        )
        for entry in meta[:needed]
    ]
    chunks = [
        tuple(builds[i * team_size : (i + 1) * team_size]) for i in range(teams)
    ]
    return list(combinations(chunks, 2))


def play(
    gm: GameMaster,
    team_one: Sequence[Build],
    team_two: Sequence[Build],
    ai_one: AiFactory,
    ai_two: AiFactory,
) -> Tuple[float, float]:
    """
    Play one battle and return both sides' ratings, seat one first.

    Pokemon are built fresh rather than reset, so nothing carries over between
    battles in a long sweep.
    """
    mons_one = [instantiate(gm, build) for build in team_one]
    mons_two = [instantiate(gm, build) for build in team_two]

    player_one = Player(team=mons_one)
    player_one.ai = ai_one(player_one)
    player_two = Player(team=mons_two)
    player_two.ai = ai_two(player_two)

    PvpBattle(player_one, player_two).simulate()

    return team_rating(mons_one, mons_two), team_rating(mons_two, mons_one)


def score_ai(
    gm: GameMaster,
    under_test: AiFactory,
    suite: Sequence[Pairing],
    league: str = "",
    reference: AiFactory = NaiveAI,
    progress: Optional[Callable[[int, int], None]] = None,
) -> FitnessReport:
    """
    Score `under_test` against `reference` over `suite`.

    500 means the two are indistinguishable. Deterministic: two runs of the
    same suite against the same AI give the same number.
    """
    results: List[MatchupResult] = []

    for index, (team_one, team_two) in enumerate(suite):
        # The AI takes team one in seat one, then team two in seat two, and the
        # reference takes exactly the mirror of that. Anything the teams or the
        # seats are worth is held by both AIs equally and cancels.
        as_one, _ = play(gm, team_one, team_two, under_test, reference)
        _, as_two = play(gm, team_one, team_two, reference, under_test)

        results.append(
            MatchupResult(
                team_one=tuple(b.species_id for b in team_one),
                team_two=tuple(b.species_id for b in team_two),
                as_one=as_one,
                as_two=as_two,
            )
        )
        if progress:
            progress(index + 1, len(suite))

    score = sum(r.score for r in results) / len(results) if results else EVEN
    return FitnessReport(
        score=score, league=league, battles=len(results) * 2, results=results
    )


def compare(
    gm: GameMaster,
    candidates: Dict[str, AiFactory],
    suite: Sequence[Pairing],
    league: str = "",
    reference: AiFactory = NaiveAI,
    progress: Optional[Callable[[str, int, int], None]] = None,
) -> Dict[str, FitnessReport]:
    """Score several AIs over one suite, so their numbers are comparable."""

    def relay(name: str) -> Optional[Callable[[int, int], None]]:
        if progress is None:
            return None
        return lambda done, total: progress(name, done, total)

    return {
        name: score_ai(
            gm,
            factory,
            suite,
            league=league,
            reference=reference,
            progress=relay(name),
        )
        for name, factory in candidates.items()
    }
