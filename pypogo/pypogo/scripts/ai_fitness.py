"""
Score every battle AI against a reference, over a fixed suite of 3v3 matchups.

    python3 pypogo/scripts/ai_fitness.py                 # all tiers, 4 teams
    python3 pypogo/scripts/ai_fitness.py --teams 8       # a wider, slower suite
    python3 pypogo/scripts/ai_fitness.py --league ultra
    python3 pypogo/scripts/ai_fitness.py --detail        # per-pairing breakdown

500 means "plays the same as the reference"; the distance from 500 is the
margin in rating points. See `pypogo/ai/fitness.py` for why that anchor holds.

Run from the pypogo/ directory. Cost is quadratic in `--teams`: 4 teams is six
pairings and about two seconds per AI, 8 teams is 28 pairings and about eight.
Read the spread before believing a small difference -- per-pairing standard
deviation is around 50 rating points, so at six pairings anything under ~40
points apart is indistinguishable.
"""

import argparse
import statistics
import time
from typing import Dict

from pypogo.ai.fitness import AiFactory, build_suite, compare, league_meta
from pypogo.ai.naive import NaiveAI
from pypogo.ai.pvpoke.constants import AILevel
from pypogo.ai.pvpoke.pvpoke import PvPokeAI
from pypogo.game_master.game_master import GameMaster
from pypogo.meta import LEAGUE_KEYS


def tier_factory(tier: AILevel) -> AiFactory:
    """Bind an AI level into a factory. A closure, so mypy can see the type."""
    return lambda player: PvPokeAI(player, level=tier)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--league", default="great", choices=sorted(LEAGUE_KEYS))
    parser.add_argument(
        "--teams", type=int, default=4, help="Teams to draw from the meta (pairs grow quadratically)"
    )
    parser.add_argument(
        "--detail", action="store_true", help="Print each AI's worst pairings"
    )
    args = parser.parse_args(argv)

    gm = GameMaster()
    suite = build_suite(league_meta(args.league), teams=args.teams)

    candidates: Dict[str, AiFactory] = {"naive (self)": NaiveAI}
    candidates.update(
        {level.name.lower(): tier_factory(level) for level in AILevel}
    )

    print(
        f"{args.league} league, {args.teams} teams, {len(suite)} pairings, "
        f"{len(suite) * 2} battles per AI, reference = NaiveAI\n"
    )
    started = time.time()
    reports = compare(gm, candidates, suite, league=args.league)

    print(f"{'ai':14s} {'score':>8s} {'edge':>8s} {'sd':>7s}  {'range':>11s}")
    for name, report in reports.items():
        per = [r.score for r in report.results]
        spread = statistics.pstdev(per) if len(per) > 1 else 0.0
        print(
            f"{name:14s} {report.score:8.1f} {report.edge:+8.1f} {spread:7.1f}  "
            f"{min(per):5.0f}-{max(per):<5.0f}"
        )

    # The standard error is what says whether two AIs actually differ. Printing
    # it beside the scores is the difference between a benchmark and a number
    # people over-read.
    any_report = next(iter(reports.values()))
    pairings = len(any_report.results)
    typical_sd = statistics.mean(
        statistics.pstdev([r.score for r in rep.results])
        for rep in reports.values()
        if len(rep.results) > 1
    )
    print(
        f"\nstandard error at {pairings} pairings: ~{typical_sd / pairings**0.5:.0f} "
        "rating points. Treat smaller differences as noise."
    )

    if args.detail:
        for name, report in reports.items():
            if name.startswith("naive"):
                continue
            print(f"\n{name} -- worst pairings")
            for result in report.worst(3):
                print(
                    f"  {result.score:6.1f}  {'/'.join(result.team_one)}"
                    f"  vs  {'/'.join(result.team_two)}"
                )

    print(f"\n{time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
