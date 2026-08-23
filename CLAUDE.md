# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project direction

PvPogo is a PvP battle simulator and team builder in the spirit of pvpoke.com, being rebuilt around
agentic AI / ML and a stronger UI/UX.

**Hard constraint: ship nothing copyrighted by Pokémon.** The current code does *not* yet honor this —
it is derived from Niantic's Game Master and is saturated with protected material: `gm_latest.json`
(11 MB verbatim game data), `pokemon.json`, `moves.json`, species names and Pokédex numbers hardcoded
in `app/team/page.tsx`, the 18 canonical types in `poketypes.py`, and Pokémon-named identifiers
throughout. Treat all of it as legacy scaffolding to be replaced with original species/type/move data
behind the same interfaces. When adding code, prefer generic domain vocabulary (`species`, `creature`,
`element`) over the Pokémon-specific naming used by the existing modules.

## The gate

`npm run verify` (eslint, tsc, ruff, mypy, pytest -- ~15s) is the single source of
truth for "is the tree green". `npm run verify:all` adds a production build and the
Playwright E2E suite. CI runs the latter on every push; a Claude Code `Stop` hook
(`.claude/settings.json` -> `scripts/stop-gate.sh`) runs the fast one and blocks the
turn from ending while it is red.

Run it before claiming anything works. Do not add a check that is red on arrival --
a gate that is red by default gets ignored, which is worse than no gate.

The Python half wants `pypogo/.venv`:

```bash
python3 -m venv pypogo/.venv
pypogo/.venv/bin/pip install -r pypogo/requirements-dev.txt -e pypogo
```

## Commands

Frontend, from the repo root:

```bash
npm install
npm run dev      # Next.js dev server
npm run build
npm run lint     # ESLint CLI (migrated off the deprecated `next lint`)
npm run lint:fix
```

`.eslintignore` must keep excluding `pypogo` — the ESLint CLI walks the whole tree and picks up stray
configs from Jupyter lab extensions inside `pypogo/venv`, which aborts the run.

Python engine — **must run from `pypogo/`**, since fixtures and Game Master JSON are opened via paths
relative to the CWD (`pypogo/tests/fixtures/...`), not relative to the module:

```bash
cd pypogo
pip install -e .
python3 -m pytest -q                                   # full suite
python3 -m pytest pypogo/tests/test_battle.py          # single file
python3 -m pytest pypogo/tests/test_battle.py::PvpBattleTests::test_simulate_battle # single test
python3 pypogo/scripts/battle_demo.py                  # one 3v3 battle, dumps history to a txt file
python3 pypogo/scripts/simulation_demo.py              # round-robin over all 3-of-6 team combos
```

The suite is green (84 tests). Results are deterministic, so a diff in the roster-performance numbers
means real behaviour changed, not flake.

Django app (`pypogo/pokexperience/`) expects a local MySQL database named `pvpogo`; credentials are
hardcoded in `pokexperience/pokexperience/settings.py`.

```bash
cd pypogo/pokexperience
python3 manage.py migrate
python3 manage.py runserver
python3 manage.py load_json_to_db     # resolves the bundled JSON off the pypogo package
```

## Architecture

### Two disconnected halves

The Next.js frontend and the Python engine share no API, no schema, and no build. `app/team/page.tsx`
hardcodes its own ~150-entry species list and `app/team/types.ts` defines a `Pokemon` shape unrelated
to `pypogo.pokemon.Pokemon`. Wiring these together is unbuilt work, not something to look for.

### Battle engine (`pypogo/pypogo/`)

`PvpBattle.simulate()` is a discrete turn loop — one turn is 500 ms of game time, and every duration
in `constants.py` is derived from that (`BATTLE_TURNS`, `SWITCH_TURNS`, `CHARGED_TURNS`). Each turn:
both players are asked for an action, actions resolve, then cooldowns/switch timers decrement.

Control flow is a phase machine over `BattlePhase` (`constants.py`): `NEUTRAL` is the normal
action-exchange state; the `SUSPEND_*` phases model the real game's interruptions — a charged move
freezing the clock for the shield decision, or one/both Pokémon fainting and needing a replacement.
`_eval_turn()` dispatches on the current phase, so new battle mechanics belong in a phase handler
rather than inline in the loop.

Action legality lives in **one** place: `AInterface.is_valid_action()` in `ai/interface.py`. It
encodes every rule about what a player may do in a given phase (energy for charged moves, shield
availability, switch timers, remaining Pokémon). `PvpBattle` trusts it. Any new action type must be
taught to that method.

`OneVsOneBattle.simulate()` (bottom of `battle.py`) is the analysis primitive: it wraps two single-
Pokémon `Player`s in a full `PvpBattle` and returns a 0–1000 **battle rating** — half from damage
dealt, half from HP retained. Every roster/team heuristic is built on this number.

### Domain model layering

Three distinct levels, easy to confuse:

- `PokedexEntry` (`pokedex.py`) — static species data: base stats, types, legal move pools, family.
- `Pokemon` (`pokemon.py`) — a species instantiated with a level, IVs, and a chosen moveset. Derives
  CP and effective stats through `CP_MULTIPLIER` and `stats.py`.
- `PvpPokemon` (`pokemon.py`) — the battle-mutable subclass: current HP, energy, cooldown turns, and
  a `BuffState`. Simulations call `.clone()` before and `.full_reset()` between battles; forgetting
  either silently corrupts multi-battle runs.

`Move` vs `PvpMove` mirrors this split — `PvpMove` binds a move to a specific attacker/defender pair
so `.damage` is a resolved number.

### Data ingestion

`GameMaster` (`game_master/game_master.py`) is a **singleton** that parses the 11 MB `gm_latest.json`
on first construction, filtering keys with the regexes at the top of the file to skip costume and
event variants. It is the factory for everything else: `GM.get_pokemon(species_id, fast_move_id,
charged_move_ids, level, ivs)` returns a fully built `PvpPokemon`. Test fixtures instantiate it at
module import, so importing `pypogo.tests.utils` costs a multi-second parse.

### AI layer — the extension point

`AInterface` (`ai/interface.py`) is the ABC every AI implements: `select_team`, `decide_action`,
`decide_switch`, `decide_shield`. This is where agentic/ML work plugs in.

`decide_action` returns an `(AIStatus, PvpAction)` pair and takes only the battle phase. Context an
AI needs beyond that — the opposing player, the current turn — is reached through the `opponent` and
`turn` helpers on `AInterface`, which read the `opponent`/`battle` handles `PvpBattle.__init__`
attaches to each `Player` via `Player.enter_battle`. That is why battle code can keep calling
`decide_action(phase)` at ~14 call sites without threading context through.

Two implementations:

- `ai/naive.py` — `NaiveAI`, the default. Picks the first legal action from a fixed priority list.
- `ai/pvpoke/` — `PvPokeAI`, a port of pvpoke's heuristic AI. Runnable at all four `AILevel` tiers.
  It guesses the opponent's charged move and weighs shielding, weights switch targets by simulated
  matchup, and picks teams by `DecisionType`. Against `NaiveAI` the tiers grade as expected
  (NOVICE 7/20 → CHAMPION 20/20), driven mostly by the shielding heuristic.

  **Known gap:** nothing selects a non-`DEFAULT` `Strategy` yet, so the switch/overfarm branches in
  `_decide_battle_action` stay dormant in normal play and archetypes differ only in how they shield.
  Implementing that state machine is the next piece of work. A naive re-evaluate-every-turn version
  was tried and made CHAMPION *worse* than NOVICE by thrashing (2,087 strategy transitions in 10
  battles, because CHAMPION's `reaction_time` is 0) — it needs real hysteresis.

  `run_scenario` is memoised per-AI (`_scenario_cache`); each uncached call costs nine simulated
  battles, and the shield/switch heuristics ask about the same matchup repeatedly.

`ai/pvpoke/roster_analysis.py` and `team_generation.py` *do* work and are the interesting prior art
for the ML direction: `RosterAnalyzer.run_scenario` sweeps all 3×3 shield combinations, weights them
`[4, 4, 1]`, and averages into a matchup score; `TeamGenerator` then composes lead / bodyguard /
closer teams from those scores. That brute-force scoring is the natural baseline to beat.

### Django app (`pypogo/pokexperience/`)

Mostly scaffolding — one placeholder view. Its value is `app/models.py`, which mirrors `PokedexEntry`
and `Move` as ORM tables, plus the `load_json_to_db` management command that ingests the Game Master
JSON. It duplicates rather than imports the `pypogo` dataclasses; the two will drift.

## Repo-level gotchas

- **`gm_latest.json` is 11 MB of verbatim Niantic Game Master data, now in git history.** It was
  committed deliberately so the suite runs on a fresh clone. It is also exactly the material the
  no-Pokémon-IP constraint targets, so the de-branding work has to rewrite it out of history, not just
  delete the file.
- **Anything defining `__eq__` needs `__hash__` with it.** Python sets `__hash__ = None` when you
  define `__eq__`, silently making instances unusable as dict keys or set members. `BattlePhase`,
  `PvpAction`, `AIStatus`, `PokedexEntry`, and `StatsCombo` all hit this and are now fixed; keep the
  pair together in anything new. `pypogo/tests/test_value_semantics.py` guards it.
- **The Django models duplicate the `pypogo` dataclasses** rather than importing them, so schema
  changes need doing twice. `PokedexEntry.species_id` — not `dex_number` — is the unique key: 112 dex
  numbers carry more than one form (`stunfisk` and `stunfisk_galarian` are both 618).
- **`.eslintignore` must exclude `pypogo`.** The ESLint CLI otherwise walks into `pypogo/venv` and
  aborts on a Jupyter lab extension's config.
- **`npm install` needs `.npmrc`'s `legacy-peer-deps`.** `@formspree/react` declares a peer range of
  react@^16-18 while the project is on React 19; without the flag npm refuses to resolve the tree.
- **The engine has no third-party runtime dependencies** -- it is pure stdlib, and `pypogo/setup.py`
  declares no `install_requires`. Keep it that way: an undeclared `attrs` import used to work only
  because it happened to be present in one contributor's interpreter, and broke in a clean venv.
- **`pypogo/venv/` is a broken leftover** (no interpreter in it). The real one is `pypogo/.venv`.
  Both are gitignored; deleting the old one is safe but nobody has.

## Conventions

`AGENTS.md` holds the style guide for both stacks (TypeScript/HeroUI/Tailwind and Python). Follow it;
don't restate it here. Two points worth reinforcing: `@/*` maps to the repo root in `tsconfig.json`,
and HeroUI components require `"use client"` in App Router files.
