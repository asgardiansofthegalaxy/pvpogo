# Handoff

State as of commit `19a6a07` on branch `carlos/dev`. `main` is untouched at
`3a4fe98`; the branch is 8 commits ahead.

## Get running

```bash
npm ci                                   # .npmrc sets legacy-peer-deps; see the comment there
python3 -m venv pypogo/.venv
pypogo/.venv/bin/pip install -r pypogo/requirements-dev.txt -e pypogo

npm run verify        # eslint, tsc, ruff, mypy, pytest  (~15s)
npm run verify:all    # the above + production build + Playwright  (~60s)
npm run dev
```

Green baseline: **108 Python tests, 11 Playwright tests, ruff/mypy/tsc/eslint
clean.** If any of that is red on arrival, fix it before starting new work --
the gate is only useful while it is trusted.

Read `CLAUDE.md` first, then `DISCLAIMER.md` before touching anything that
loads data or renders a species.

## What is already built

| Area | State |
| --- | --- |
| Verification gate | `scripts/verify.sh`, GitHub Actions, and a Claude Code `Stop` hook that blocks a turn ending on a red tree |
| Data policy | Derived dataset only; no publisher artwork, no raw Game Master export. Enforced by `test_ip_hygiene.py` |
| Dataset validator | `test_dataset_invariants.py` -- referential integrity, stat ranges, known gaps pinned |
| Battle engine | Turn-based phase machine, damage/CP formulas match the live game's behaviour |
| Battle AI | `NaiveAI` and `PvPokeAI` (4 tiers, graded 7/14/13/20 of 20 vs naive) |
| Analysis | `RosterAnalyzer` (matchup ratings) and `TeamGenerator` (lead/bodyguard/closer) -- **working, but unreachable from the web** |
| Website | Team builder on the real 1279-species dataset: league caps, auto-levelling, moveset/level/IV controls, live CP |

## The decision that was blocking, now settled by measurement

Exposing the simulator to the web looked like a hard fork -- Python service vs.
porting the engine to TypeScript. Benchmarking the analysis primitive settles it
for the near term:

```
single 1v1 battle                6.5 ms
run_scenario (9 shield combos)    68 ms
top-100 meta matrix     90,000 battles  ~10 min single-core, offline
```

**Precompute the meta matrix.** A top-100-per-league matchup matrix builds in
about ten minutes offline and ships as static JSON, exactly like the rest of the
dataset. That covers the feature people actually want -- "how does my team fare
against the meta" -- with no server, no engine duplication, and no deployment
change.

Only *arbitrary* interactive matchups (any species, any moveset, any IVs) need a
live engine, and 1279² is far too large to precompute. Defer the
service-vs-port decision until something actually requires that. Do not build a
service now.

## Next actions, in order

### 1. Precompute and ship the meta matchup matrix

The highest-value unbuilt thing, and the reason the analysis code exists.

- Add `pypogo/pypogo/scripts/build_matchups.py`, following the shape of
  `build_dataset.py` (`--check` for drift, writes into the engine's data dir).
- Define the meta slice per league. There is no ranking data in the repo yet, so
  derive one -- a reasonable first cut is every species whose max CP under the
  cap is within some band, scored by stat product.
- Output: `matchups.<league>.json`, keyed by species pair, holding the
  shield-weighted rating `RosterAnalyzer.run_scenario` already produces.
- Extend `scripts/build-web-data.mjs` to trim it for the browser. Watch the
  payload: a dense 100x100 matrix is 10,000 entries. Store ratings as integers
  and consider only the upper triangle.
- Add invariants to `test_dataset_invariants.py`: every referenced species
  exists, ratings are 0-1000, the matrix is complete.

Acceptance: the team builder shows, for each pick, its best and worst matchups
against the meta, sourced from precomputed data with no server.

### 2. Team-level matchup analysis in the UI

With the matrix shipped, `RosterAnalyzer.calculate_roster_performance`'s logic
becomes a client-side lookup. Show coverage gaps -- which meta picks beat all
three of the user's choices. That is the answer a team builder exists to give.

### 3. Move rankings, so defaults stop being wrong

Azumarill currently defaults to Rock Smash because that is the order the dataset
lists its moves. Rank moves by damage-per-energy and turn efficiency, ship the
ranking, and default to the best pair. Small change, large credibility gain.

### 4. IV optimiser

`StatsRanker.get_iv_rankings` already exists in Python and is unreachable. For a
single species under a CP cap this is ~4096 combinations x ~100 levels, fast
enough to run client-side. Give the builder a "best IVs for this league" action.

## Known gaps and traps

- **`PvPokeAI`'s strategy state machine is unimplemented.** Nothing selects a
  non-`DEFAULT` `Strategy`, so the switch and overfarm branches never run and
  archetypes differ only in how they shield. A naive re-evaluate-every-turn
  version was tried and made CHAMPION play *worse* than NOVICE by thrashing
  (2,087 strategy transitions across 10 battles, because CHAMPION's
  `reaction_time` is 0). It needs real hysteresis. **Do not tune the AI without
  a fitness function** -- build a fixed benchmark of matchups with expected
  outcomes first, which is also the on-ramp for the ML work.
- **`ScenarioType` has no effect.** All four types produce identical numbers
  because shield baiting is not modelled in the engine. Implementing baiting
  would change every roster number, including pinned test expectations.
- **`gm_latest.json` is still in git history.** Untracked and gitignored now,
  but earlier commits hold an 11 MB copy of Niantic's export. Needs
  `git filter-repo` **before this repo is ever public**.
- **The product name.** "PvPogo" evokes Pokémon GO directly, and a product name
  is where nominative use is weakest -- it is branding, not identification.
  Everything else is defensible; this is the piece to change, and it is cheaper
  now than after there are users.
- **`pypogo/venv/` is a broken leftover** with no interpreter. The real one is
  `pypogo/.venv`. Both gitignored.
- **The Django app** (`pypogo/pokexperience/`) is scaffolding with one
  placeholder view and duplicated models. Decide whether it earns its place;
  nothing currently depends on it.
- **`public/data/` is generated, not committed.** `predev`/`prebuild` rebuild it
  from the engine dataset. Do not commit it -- that would be a third copy free
  to drift.

## Conventions worth not relearning

- `AGENTS.md` holds the style guide. `@/*` maps to the repo root.
- Python must run from `pypogo/`; fixtures resolve relative to that directory.
- Anything defining `__eq__` needs `__hash__` beside it -- five classes here hit
  that trap already.
- Do not add a check to the gate that is red on arrival. A gate that is red by
  default gets ignored, which is worse than no gate.
- When wiring a scroll container inside a grid or flex parent, set `min-w-0` or
  the track sizes to content and the page scrolls sideways.
