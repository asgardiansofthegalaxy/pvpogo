"""
Export the move ranking as a file the website's build step can read.

`movesets.py` decides which moves a species should be built with, and the
matchup matrices are computed on its answer. The team builder needs the same
answer -- otherwise it hands users the Rock Smash Azumarill the matrix
carefully avoids -- but `scripts/build-web-data.mjs` reads JSON only and has no
Python toolchain, by design. So the ranking ships as a derived file beside the
dataset and the exported species list is ordered by it.

    python3 pypogo/scripts/build_movesets.py            # write movesets.json
    python3 pypogo/scripts/build_movesets.py --check    # verify no drift

Run from the pypogo/ directory. Unlike the matchup matrices this is pure
arithmetic over the dataset -- well under a second -- so the drift check is
cheap enough to also live in the gate, as `tests/test_movesets.py`.
"""

import argparse
import json
import os
import sys

from pypogo.game_master.game_master import CWD, GameMaster
from pypogo.movesets import MOVESETS_FILE, rankings_payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the committed file differs from a fresh build",
    )
    args = parser.parse_args(argv)

    gm = GameMaster()
    payload = rankings_payload(gm.pokedex, gm.moves)
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    path = os.path.join(CWD, MOVESETS_FILE)

    if args.check:
        existing = open(path).read() if os.path.exists(path) else None
        if existing != serialized:
            print(f"{MOVESETS_FILE} differs from a fresh build", file=sys.stderr)
            return 1
        print(f"{MOVESETS_FILE} matches a fresh build")
        return 0

    with open(path, "w") as fp:
        fp.write(serialized)

    ranked = payload["rankings"]
    skipped = len(gm.pokedex) - len(ranked)
    print(
        f"wrote {MOVESETS_FILE}: {len(ranked)} species, "
        f"{len(serialized) / 1024:.0f} KB, {skipped} without a usable pool"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
