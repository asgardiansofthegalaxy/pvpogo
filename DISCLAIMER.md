# Legal notice and data policy

This is an unofficial, fan-made PvP analysis tool. It is **not affiliated with,
endorsed by, sponsored by, or approved by** Nintendo, The Pokémon Company,
Game Freak, Creatures Inc., or Niantic, Inc.

Pokémon and all related names are trademarks of their respective owners. They
are used here **nominatively** — that is, only to refer to the actual creatures
and moves the tool analyses, because there is no other way to identify them.
No claim of ownership is made.

> This document records the project's intent and the rules it enforces in code.
> It is not legal advice. If this is ever operated commercially or at scale,
> get a lawyer to look at it.

## What this project does and does not distribute

The distinction the project runs on is between **facts and mechanics**, which
are not copyrightable, and **creative expression**, which is.

### Distributed — factual game data

`pypogo/pypogo/game_master/pokemon.json` and `moves.json` hold base stats,
typings, move pools, and move power/energy/duration values. These are
measurements of how a published game behaves. They are stored in this
project's own schema, not in the publisher's file format.

### Not distributed — publisher assets

| Asset | Why not |
| --- | --- |
| Sprites, models, official artwork | Copyrighted creative expression. The UI renders its own `SpeciesAvatar` mark instead. |
| Raw Game Master exports (`gm_latest.json`) | Niantic's own file. It is a **build input** for regenerating the derived dataset, never committed or redistributed. |
| Logos, wordmarks, trade dress | Trademarks; using them would imply endorsement. |
| Music, sound, UI chrome from the games | Copyrighted assets. |

### Regenerating the dataset

The derived files are reproducible. Supply your own copy of a Game Master
export and run:

```bash
cd pypogo
python3 pypogo/scripts/build_dataset.py --raw /path/to/game_master.json
python3 pypogo/scripts/build_dataset.py --raw /path/to/game_master.json --check   # drift check
```

The engine never reads the raw export at runtime — only the derived dataset.

## Rules enforced in code

These are tests, not good intentions. They run in `npm run verify` and fail the
build on violation. See `pypogo/pypogo/tests/test_ip_hygiene.py`.

1. No raw Game Master export is tracked in git.
2. No source file references a publisher sprite/asset host.
3. No image assets are added that could be publisher artwork.
4. This disclaimer exists and is surfaced in the app UI.

## Known gap

`gm_latest.json` was committed earlier in this repository's history and remains
in past commits even though it is untracked now. Fully removing it needs a
history rewrite (`git filter-repo`) before this repo is ever made public.
