# Handoff

State as of the IV-optimiser work on branch `carlos/dev`. `main` is untouched
at `3a4fe98`.

## Get running

```bash
npm ci                                   # .npmrc sets legacy-peer-deps; see the comment there
python3 -m venv pypogo/.venv
pypogo/.venv/bin/pip install -r pypogo/requirements-dev.txt -e pypogo

npm run verify        # eslint, tsc, ruff, mypy, pytest  (~25s)
npm run verify:all    # the above + production build + Playwright  (~75s)
npm run dev
```

Green baseline: **142 Python tests, 18 Playwright tests, ruff/mypy/tsc/eslint
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
| Battle engine | Turn-based phase machine, damage/CP formulas match the live game's behaviour. **Now genuinely deterministic** -- see below |
| Battle AI | `NaiveAI` and `PvPokeAI` (4 tiers, graded 7/14/13/20 of 20 vs naive) |
| Move ranking | `movesets.py` picks a species' moveset without simulating; measured against brute force in `test_movesets.py`. Exported as `movesets.json` and used for the website's move order and defaults |
| Meta + matchups | `meta.py` derives each league's meta and a full matchup matrix; shipped as `matchups.{great,ultra,master}.json` |
| Website | Team builder on the real 1270-species dataset, showing each pick's best and worst matchups against its league meta and what the team as a whole has no answer to. A fresh pick starts on the moveset those matchups were simulated with |

## Recent changes

### This session: the IV optimiser

`app/lib/ivs.ts` ranks all 4,096 spreads at their best level under the cap and
the team slot gained a "Best IVs" button plus a live `Rank #N of 4,096` line.
The rank is what makes the button worth pressing rather than magic: it says how
much is on the table before, and confirms the result after. All 4,096 spreads
cost ~30ms, so it runs on click; it is memoised per species and cap, keyed on
the stats object rather than on `member`, which is a fresh object on every edit.

**It does not port `StatsRanker.get_iv_rankings`.** That ranks by the *sum* of
effective stats; `meta.py` and the UI both use stat *product*, which is the PvP
measure and the reason low-attack spreads win under a cap. The two mostly agree
at the optimum -- Registeel is the widest gap of those measured, 4 stat product
in 2,405 -- so this is a correctness nit rather than a live bug, but the engine
method is the one that is out of step.

The feature exposed a coherence problem worth knowing about: the matrix is
simulated at one spread (`assumptions.ivs`, 0/15/15, which is also the
builder's default), so optimising IVs hands the user a strictly better Pokémon
than the one the ratings beside it describe. `spreadMatches` now covers IVs and
level the way `buildMatches` covers moves, and the panel says "Simulated at
0/15/15, level 23.5 — not your spread." Anything that changes a pick's spread
needs to go through it.

### Before that: team coverage

The per-pick panel said how one Pokémon fares. The team-level question -- which
meta picks beat *all* of your picks -- is now answered too, as a scan down each
meta column for the member that does best against it. No simulation: the
matrix already holds every 1v1 rating, so this is a lookup that updates as fast
as the user can click.

`build-web-data.mjs` now writes each league twice. The summary (best/worst few
plus a mean) is unchanged and still loads with the page at 82 KB gzipped;
`matchups.<league>.rows.json` carries the full matrix at 182 KB and is fetched
only once there is a team to analyse, so browsing the roster never pays for it.
The rows file repeats the meta ids in column order and `teamCoverage` refuses
to run if they disagree with the summary -- lining a row up against the wrong
opponent would be worse than showing nothing.

Two judgement calls worth knowing:

* **A mirror is not counted as the team's answer to itself.** Bringing
  Azumarill does not make you covered against Azumarill: a mirror rates ~500
  and lands within ~100 either way, so counting it would decide those rows on
  noise. The rest of the team gets measured instead, and the row carries a
  `mirror` chip so "Azumarill beats your whole team" reads as the real finding
  it is rather than a bug.
* **The threshold is a strict 500.** Even is not answered. A team that only
  scrapes a draw against something has no answer to it.

Sanity numbers on Great League: Azumarill / Registeel / Medicham answers 96 of
100; a single Azumarill answers 69; three worthless picks answer 0.

### And before that: the builder's defaults

The team builder used to hand every fresh pick `species.fastMoves[0]` -- export
order, which is not a ranking -- so it built the Rock Smash Azumarill the
matchup matrix carefully avoids, and then showed matchup numbers with an amber
"simulated with different moves" note attached to its own default. Both halves
are fixed:

* **The exported move pools are ranked.** `movesets.py` already knew the order;
  `scripts/build_movesets.py` now writes it to `movesets.json` beside the
  dataset, and `build-web-data.mjs` orders every pool by it. `build-web-data.mjs`
  deliberately has no Python toolchain, which is why the ranking travels as a
  file rather than being recomputed in JS -- duplicating the scoring is how the
  two would drift. `test_movesets.py` regenerates the file and compares, so it
  cannot go stale; the whole ranking is under a second of arithmetic, unlike the
  matchup rebuild.
* **A fresh pick starts on the simulated build.** When the league's matchup file
  is loaded, `addSpecies` takes its moveset from `builds[species]` -- which for
  a meta pick was brute-forced rather than scored. The ranked pool is the
  fallback for the moment before that file lands. The panel's ratings now
  describe the Pokémon actually in the slot.

One thing fell out of it: nine species (Necrozma, Magearna, Zeraora and friends)
declare Struggle as their entire move pool. The engine refuses to build them,
but the export's usability check ran against the *declared* pools rather than
the battle-usable ones, so the picker offered them and picking one produced a
slot with no fast move at all. The check now uses the ranking's coverage, which
is exactly the set the engine accepts -- hence 1270 species, not 1279.

### Earlier still: the matchup matrix

The website can now answer "how does this pick fare against what it will face",
which is the question a team builder exists for. It does that with **no server**:
the engine simulates every species against its league meta offline and the
result ships as static JSON, the same way the dataset does.

Three things came out of building it that matter more than the feature:

**The engine was not deterministic.** `CLAUDE.md` claimed it was. A
charge-move-priority tie called `random.seed(time.time())` on the *global* RNG,
so the same mirror match rated 481 or 518 depending on when it ran -- and it
reset the stream `PvPokeAI` draws its energy guesses from. Fixing the seeding
exposed a second, subtler bug: seeding per *battle* meant whoever was player one
won every tie in that battle, so A beat B *and* B beat A in 21 of Great League's
4,950 meta pairs. The tie is now seeded from the **pair**, so both orderings
agree, and a true mirror alternates so it rates ~500 instead of winning every
collision. `test_determinism.py` pins all of it. **Any precomputed analysis in
this repo is only meaningful because of this fix** -- before it, a `--check`
drift gate would have failed at random.

**Default movesets were costing more than they looked.** The dataset lists moves
in export order, so Azumarill led with Rock Smash. Measured against brute-force
simulation over 38 random species, building on that order gives up ~47 rating
points on average and 168 at worst -- enough to swamp the matchup signal
entirely. The heuristic in `movesets.py` gives up ~11. Both numbers are pinned in
`test_movesets.py`, so changing the scoring means arguing with a measurement.

**61 species crashed the engine.** `AInterface.is_valid_action` indexed
`charged_moves[1]` unconditionally, so any battle involving Caterpie, Iron Hands
or Flutter Mane raised `IndexError`. It now returns "not a legal action".

## Next actions, in order

### 1. A fitness function for the AI, then the strategy state machine

Unchanged from before, and still the prerequisite for any AI tuning. The
matchup matrix is now a plausible basis for the benchmark: a fixed set of
matchups with known expected outcomes.

## Known gaps and traps

- **The meta is derived, not curated.** Nothing in the Game Master says what
  people actually play and this project has no usage data, so "meta" means
  "measurably beats other strong picks under the cap". It knows nothing about
  usage, coverage or team roles. Great League's list is recognisable (Skarmory,
  Registeel, Cobalion, Bastiodon, Galarian Stunfisk, Medicham, Azumarill), but do
  not present it as a tier list. `assumptions.meta_selection` in each file
  records how it was derived.
- **Rebuilding the matchup files takes ~40 minutes** across three leagues on 16
  cores, so `--check` is a deliberate step, not part of the gate -- CI's whole
  budget is 20 minutes. `test_matchup_invariants.py` is what guards them in the
  gate: shape, referential integrity, and the two properties that only hold if
  the simulation is sound (mirrors centred on 500, `rating(a,b) + rating(b,a) ==
  1000`).
- **A mirror is only *approximately* 500** -- individual ones land within ~100
  points either way. A battle has a handful of decisive collisions and somebody
  wins each; what matters is that they are centred, which is what the test
  asserts. Do not "fix" this by tightening the per-species bound.
- **Row movesets are heuristic, meta movesets are simulated.** The ~1,100
  non-meta rows cannot afford brute force. If a row's numbers look off, that
  asymmetry is the first place to look.
- **`ScenarioType` still has no effect.** All four types produce identical
  numbers because shield baiting is not modelled. Implementing baiting would
  change every number in the matchup files.
- **`PvPokeAI`'s strategy state machine is unimplemented.** Nothing selects a
  non-`DEFAULT` `Strategy`. A naive re-evaluate-every-turn version made CHAMPION
  play *worse* than NOVICE by thrashing (2,087 strategy transitions across 10
  battles, because CHAMPION's `reaction_time` is 0). It needs real hysteresis.
  **Do not tune the AI without a fitness function.**
- **`gm_latest.json` is still in git history.** Untracked and gitignored now, but
  earlier commits hold an 11 MB copy of Niantic's export. Needs `git filter-repo`
  **before this repo is ever public**.
- **The product name.** "PvPogo" evokes Pokémon GO directly, and a product name
  is where nominative use is weakest -- it is branding, not identification.
  Everything else is defensible; this is the piece to change, and it is cheaper
  now than after there are users.
- **`pypogo/venv/` is a broken leftover** with no interpreter. The real one is
  `pypogo/.venv`. Both gitignored.
- **The Django app** (`pypogo/pokexperience/`) is scaffolding with one
  placeholder view and duplicated models. Nothing depends on it.
- **`public/data/` is generated, not committed.** `predev`/`prebuild` rebuild it
  from the engine dataset, `movesets.json` and the matchup files.
- **`StatsRanker` ranks IVs by stat sum, the rest of the project by stat
  product.** Nothing depends on `get_iv_rankings` today, so it is inert rather
  than wrong-in-production, but do not reach for it as the reference: the web
  optimiser in `app/lib/ivs.ts` and `meta.py::stat_product` are the measure.
- **Coverage is 1v1, not 3v3.** It answers "does anything on this team beat
  that", which is the question worth asking while picking. It knows nothing
  about switching, shield pressure across a match, or lead advantage. The panel
  says so; do not let a future feature quietly imply otherwise.
- **Switching league does not re-pick a team's movesets.** Level is re-capped,
  moves are left alone, because clobbering a choice the user made is worse than
  the alternative. 89 species have a different simulated build in Great and
  Ultra, so the panel's "simulated with different moves" note can appear after a
  league switch. That is the note doing its job, not a bug.

## Conventions worth not relearning

- `AGENTS.md` holds the style guide. `@/*` maps to the repo root.
- Python must run from `pypogo/`; fixtures resolve relative to that directory.
- Anything defining `__eq__` needs `__hash__` beside it.
- Anything indexing `charged_moves[1]` needs a length check -- 61 species have
  only one.
- Do not add a check to the gate that is red on arrival.
- When wiring a scroll container inside a grid or flex parent, set `min-w-0` or
  the track sizes to content and the page scrolls sideways.
- In Playwright, scope team-panel queries to `getByRole("region", { name: "Your
  team" })`. The species picker renders list items too, and its entries come
  first in the DOM.
