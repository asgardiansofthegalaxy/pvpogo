"""
Rebuild the derived dataset (pokemon.json, moves.json) from a raw Game Master export.

The engine runs on the derived dataset -- base stats, typings, move pools and
move values, i.e. facts about how the live game behaves. Niantic's raw export is
a build input only and is not distributed with this project; supply your own
copy to regenerate. See DISCLAIMER.md.

    python3 pypogo/scripts/build_dataset.py --raw /path/to/gm_latest.json
    python3 pypogo/scripts/build_dataset.py --raw ... --check   # CI: verify no drift

Run from the pypogo/ directory.
"""

import argparse
import json
import os
import sys

from pypogo.game_master.game_master import (
    CWD,
    MOVES_FILE,
    POKEDEX_FILE,
    RAW_GAME_MASTER_FILE,
    GameMaster,
)


def build(raw_path: str) -> tuple[dict, dict]:
    """Parse a raw Game Master export into the two derived tables."""
    gm_data = GameMaster._load_gm_data(raw_path)
    grouped = GameMaster._get_grouped_keys(gm_data)

    moves = GameMaster._load_moves(grouped["move"])
    species = GameMaster._load_pokedex_pokemon(grouped["pokemon"])

    # moves.json is keyed by display name. Fast moves already end in "Fast"
    # because their raw uniqueId carries a _FAST suffix, which is what keeps
    # them from colliding with same-named charged moves.
    moves_out = {move.name: move.to_dict() for move in moves.values()}

    species_out = {sid: entry.to_dict() for sid, entry in species.items()}
    return species_out, moves_out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw",
        default=os.path.join(CWD, RAW_GAME_MASTER_FILE),
        help="Path to a raw Game Master export (not distributed with this project)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the committed dataset differs from a fresh build",
    )
    args = parser.parse_args(argv)

    species, moves = build(args.raw)

    targets = [(POKEDEX_FILE, species), (MOVES_FILE, moves)]
    drifted = []

    for filename, payload in targets:
        path = os.path.join(CWD, filename)
        serialized = json.dumps(payload, indent=1, sort_keys=True) + "\n"

        if args.check:
            existing = open(path).read() if os.path.exists(path) else None
            if existing != serialized:
                drifted.append(filename)
            continue

        with open(path, "w") as fp:
            fp.write(serialized)
        print(f"wrote {filename}: {len(payload)} entries")

    if args.check:
        if drifted:
            print(f"dataset drift in: {', '.join(drifted)}", file=sys.stderr)
            return 1
        print("dataset matches a fresh build")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
