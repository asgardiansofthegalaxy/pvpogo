"""
Precompute each league's meta and the matchup matrix over it.

The website needs to answer "how does this pick fare against what it will
face" without a Python service behind it. A matchup costs ~30ms to simulate,
so a league is minutes of offline work and the answer ships as a static file,
the same way the derived dataset does.

    python3 pypogo/scripts/build_matchups.py                    # all three leagues
    python3 pypogo/scripts/build_matchups.py --league great
    python3 pypogo/scripts/build_matchups.py --check            # CI: verify no drift
    python3 pypogo/scripts/build_matchups.py --quick --size 20  # a fast, rough pass

Run from the pypogo/ directory. Expect roughly five minutes per league on a
16-core machine; `--jobs` controls the fan-out.
"""

import argparse
import json
import os
import sys
import time

from pypogo.game_master.game_master import CWD, GameMaster
from pypogo.meta import (
    DEFAULT_META_SIZE,
    LEAGUE_KEYS,
    build_league,
    matchups_filename,
)


def _progress(league: str):
    """Single-line progress, since a full build is minutes per league."""
    current_label = ""
    started = time.time()

    def report(label: str, done: int, total: int) -> None:
        nonlocal current_label, started
        if label != current_label:
            current_label = label
            started = time.time()
        if done != total and done % 25:
            return
        end = "\n" if done == total else "\r"
        print(
            f"  {league:6s} {label:6s} {done:5d}/{total:<5d} {time.time() - started:6.1f}s",
            end=end,
            flush=True,
        )

    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--league",
        action="append",
        choices=sorted(LEAGUE_KEYS),
        help="Build one league (repeatable). Defaults to all three.",
    )
    parser.add_argument(
        "--size", type=int, default=DEFAULT_META_SIZE, help="Species in the meta"
    )
    parser.add_argument(
        "--jobs", type=int, default=0, help="Worker processes (default: all cores)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip the moveset refinement pass. Faster, and the meta's movesets "
        "stay heuristic rather than simulated.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the committed files differ from a fresh build",
    )
    args = parser.parse_args(argv)

    leagues = args.league or sorted(LEAGUE_KEYS)
    gm = GameMaster()
    drifted = []

    for league in leagues:
        started = time.time()
        payload = build_league(
            gm,
            league,
            size=args.size,
            jobs=args.jobs,
            refine=not args.quick,
            progress=_progress(league),
        )
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        path = os.path.join(CWD, matchups_filename(league))

        if args.check:
            existing = open(path).read() if os.path.exists(path) else None
            if existing != serialized:
                drifted.append(matchups_filename(league))
            continue

        with open(path, "w") as fp:
            fp.write(serialized)
        print(
            f"  wrote {matchups_filename(league)}: {len(payload['meta'])} meta, "
            f"{len(payload['ratings'])} rows, {len(serialized) / 1024:.0f} KB, "
            f"{time.time() - started:.0f}s"
        )

    if args.check:
        if drifted:
            print(f"matchup drift in: {', '.join(drifted)}", file=sys.stderr)
            return 1
        print("matchups match a fresh build")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
