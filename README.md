# PvPogo

A PvP battle simulator and team builder in the spirit of [pvpoke.com](https://pvpoke.com),
being rebuilt around agentic AI, machine learning, and a stronger UI/UX.

> **Constraint:** the project ships nothing copyrighted by Pokémon. The current
> code does not yet honor this — it is derived from Niantic's Game Master and
> carries protected species, type, and move data throughout. Treat that as
> legacy scaffolding to be replaced with original data behind the same
> interfaces. See `CLAUDE.md` for detail.

## Layout

| Path | What it is |
| --- | --- |
| `app/` | Next.js 15 App Router frontend (React 19, HeroUI, Tailwind) |
| `pypogo/pypogo/` | Python battle engine, roster analysis, and battle AIs |
| `pypogo/pokexperience/` | Django app exposing the data over an ORM (scaffolding) |

The frontend and the Python engine are not yet connected — no shared API or
schema. Wiring them together is open work.

## Verification gate

One command runs everything. This is what CI runs and what the Claude Code
Stop hook enforces, so an agent cannot finish a turn with the tree red.

```bash
npm run verify        # fast: eslint, tsc, ruff, mypy, pytest (~15s)
npm run verify:all    # the above plus a production build and Playwright E2E
```

First-time setup for the Python half:

```bash
python3 -m venv pypogo/.venv
pypogo/.venv/bin/pip install -r pypogo/requirements-dev.txt -e pypogo
```

`scripts/verify.sh` falls back to whatever `python3` is on PATH when that venv
is missing, which is how CI runs it.

## Frontend

Requires Node 18+.

```bash
npm install
npm run dev        # dev server on http://localhost:3000
npm run build
npm run start
npm run lint       # ESLint CLI
npm run lint:fix
npm run typecheck  # tsc --noEmit
npm run test:e2e   # Playwright (builds and serves the app itself)
```

`npm install` needs the `legacy-peer-deps` setting in `.npmrc`; see the comment
there.

## Python engine

Requires Python 3.11+. **Run from `pypogo/`** — fixtures and Game Master data
are opened relative to that directory.

```bash
cd pypogo
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install pytest

python3 -m pytest -q                                    # full suite
python3 -m pytest pypogo/tests/test_battle.py           # one file
python3 -m pytest pypogo/tests/test_battle.py::PvpBattleTests::test_simulate_battle
```

Demo scripts:

```bash
python3 pypogo/scripts/battle_demo.py       # one 3v3 battle, writes its history to a txt file
python3 pypogo/scripts/simulation_demo.py   # round-robin over every 3-of-6 team combination
```

### Battle AIs

Both implement `pypogo.ai.interface.AInterface`, and a `PvpBattle` gives each
player a handle on its opponent so an AI can read battle context.

```python
from pypogo.ai.pvpoke.constants import AILevel
from pypogo.ai.pvpoke.pvpoke import PvPokeAI
from pypogo.battle import BattlePhase, PvpBattle
from pypogo.player import Player
from pypogo.tests.utils import load_teams

team_one, team_two = load_teams()
player, opponent = Player(team=team_one), Player(team=team_two)
player.ai = PvPokeAI(player, level=AILevel.CHAMPION)   # NOVICE / RIVAL / ELITE / CHAMPION

battle = PvpBattle(player, opponent)
battle.phase = BattlePhase.COUNTDOWN
battle.simulate()
print(battle.get_battle_winner())
```

`NaiveAI` is the default and simply plays the first legal action. `PvPokeAI`
adds shield-guessing, switch weighting, and team selection graded by archetype.

## Django app

Expects a local MySQL database named `pvpogo`; credentials are currently
hardcoded in `pokexperience/pokexperience/settings.py`.

```bash
cd pypogo/pokexperience
python3 manage.py migrate
python3 manage.py load_json_to_db    # ingest Game Master JSON into the DB
python3 manage.py runserver
```

`load_json_to_db` resolves the bundled JSON off the installed `pypogo` package,
so it works from any directory. Override with `--pokemon-json` / `--moves-json`.
