"""
Deriving a league's meta and the matchup matrix over it.

`RosterAnalyzer` can already tell you how one Pokemon fares against another.
What the website needs is that answer for every pick a user might make against
the picks they are likely to face -- and it needs it without a running Python
service. Both halves of that are solved by precomputing: a matchup costs about
30ms, so a league's worth is minutes of offline work and a static file.

The awkward part is that "the meta" is not in the dataset. Nothing in the Game
Master says which species people actually play, and this project has no usage
data, so the meta here is *derived*: the species that measurably win against
other strong species under the league's CP cap. That is an honest definition
with a real limitation -- it knows nothing about usage, coverage, or team
roles, so it is a strong-picks list, not a tier list. `MetaSelection.method`
records how a shipped file was derived so a stale one can be spotted.

Three stages, each narrowing the field cheaply enough to afford the next:

1. Rank every distinct species by stat product at its best legal level. This
   is a coarse "can it compete under this cap at all" filter, and it is pure
   arithmetic.
2. Simulate the top candidates against a small panel drawn from their own top
   end, and keep the best. This is what drops the bulky-but-toothless picks
   that stat product alone rates highly.
3. Re-pick the survivors' movesets by simulation rather than heuristic, since
   these become the columns every other species is measured against and an
   error here propagates into every row.
"""

import os
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .ai.pvpoke.constants import ScenarioType
from .ai.pvpoke.roster_analysis import RosterAnalyzer
from .constants import CP_MULTIPLIER, MAX_LEVEL, League
from .game_master.game_master import GameMaster
from .movesets import ENERGY_BUDGET, best_moveset, enumerate_movesets
from .pokedex import PokedexEntry
from .pokemon import PvpPokemon
from .stats import Stats, get_cp_from_stats

#: The IV spread every build in the matrix uses. Defence/stamina-heavy spreads
#: are what a capped league rewards, and it is the spread the team builder
#: defaults to, so the shipped numbers describe the Pokemon the UI shows.
LEAGUE_IVS = Stats(0, 15, 15)

#: How many stat-product candidates get simulated in stage 2.
CANDIDATE_POOL = 250

#: How many of them form the panel candidates are scored against.
PANEL_SIZE = 20

#: Species per league in the shipped meta.
DEFAULT_META_SIZE = 100

#: How wide the moveset refinement search goes per species. Exhaustive is
#: affordable for every species except Mew, whose 4,200 legal movesets cost
#: more than the rest of a league combined; the heuristic lands within ~11
#: rating points of optimal, so refinement only needs to look around it.
REFINE_TOP_FAST = 3
REFINE_TOP_CHARGED = 5

#: Cosmetic and regional forms share a dex number. Two per number keeps the
#: genuinely distinct pairs (Stunfisk and its Galarian form, Deoxys' forms)
#: without letting eighteen Arceus typings crowd out the rest of a league.
MAX_FORMS_PER_DEX = 2

LEAGUE_KEYS: Dict[str, League] = {
    "great": League.GREAT_LEAGUE,
    "ultra": League.ULTRA_LEAGUE,
    "master": League.MASTER_LEAGUE,
}


@dataclass(frozen=True)
class Build:
    """A species pinned to the level, IVs and moveset the matrix assumes."""

    species_id: str
    level: float
    fast_move: str
    charged_moves: Tuple[str, ...]
    cp: int


@dataclass
class MetaSelection:
    """A league's meta, plus enough provenance to audit where it came from."""

    league: str
    cap: int
    builds: List[Build]
    scores: Dict[str, float] = field(default_factory=dict)
    method: str = ""


def mechanical_signature(entry: PokedexEntry) -> Tuple:
    """
    What makes two dataset entries the same Pokemon as far as a battle cares.

    The export carries 192 entries that are pure cosmetic variants -- nineteen
    Vivillon patterns, ten Furfrou trims, and a handful of `_s` duplicates
    whose stats, typing and move pools are byte-identical to the base form.
    Simulating them separately would spend real time producing identical rows.
    """
    return (
        tuple(t.value for t in entry.types),
        entry.base_stats.attack,
        entry.base_stats.defense,
        entry.base_stats.stamina,
        tuple(sorted(entry.fast_moves)),
        tuple(sorted(entry.charged_moves)),
    )


def clone_groups(gm: GameMaster) -> Dict[str, List[str]]:
    """
    Map each battle-distinct species to the dataset ids that duplicate it.

    The shortest id wins as the representative, which picks `vivillon` over
    `vivillon_meadow` and `lugia` over `lugia_s`.
    """
    groups: Dict[Tuple, List[str]] = defaultdict(list)
    for species_id, entry in gm.pokedex.items():
        if not is_buildable(entry):
            continue
        groups[mechanical_signature(entry)].append(species_id)

    out: Dict[str, List[str]] = {}
    for members in groups.values():
        members.sort(key=lambda s: (len(s), s))
        out[members[0]] = members
    return out


def is_buildable(entry: PokedexEntry) -> bool:
    """Whether `GameMaster.get_pokemon` would accept this species."""
    stats = entry.base_stats
    return bool(
        stats.attack
        and stats.defense
        and stats.stamina
        and entry.fast_moves
        and entry.charged_moves
    )


def distinct_species(gm: GameMaster) -> List[str]:
    """Every buildable species, one representative per set of mechanical clones."""
    return sorted(clone_groups(gm))


def max_level_under_cap(base: Stats, ivs: Stats, cap: int) -> Optional[float]:
    """
    Highest half-level whose CP stays under the cap, or None if even level 1 is over.

    Mirrors `maxLevelUnderCap` in app/lib/pokemon.ts. CP rises monotonically
    with level, so the first level over the cap ends the search.
    """
    best: Optional[float] = None
    level = 1.0
    while level <= MAX_LEVEL:
        if get_cp_from_stats(base, ivs, level) <= cap:
            best = level
        else:
            break
        level += 0.5
    return best


def stat_product(base: Stats, ivs: Stats, level: float) -> float:
    """
    Bulk-times-attack at a given level, the standard cheap measure of a build.

    Used only to shortlist candidates for simulation; it rates a wall with no
    offence as highly as a genuine threat, which is exactly what stage 2 fixes.
    """
    cpm = CP_MULTIPLIER[int((level - 1) * 2)]
    attack = cpm * (base.attack + ivs.attack)
    defense = cpm * (base.defense + ivs.defense)
    stamina = int(cpm * (base.stamina + ivs.stamina))
    return attack * defense * stamina / 1000


def make_build(gm: GameMaster, species_id: str, cap: int) -> Optional[Build]:
    """The league-legal build for a species, or None if it cannot make the cap."""
    entry = gm.pokedex[species_id]
    if not is_buildable(entry):
        return None

    level = max_level_under_cap(entry.base_stats, LEAGUE_IVS, cap)
    if level is None:
        return None

    try:
        fast, charged = best_moveset(entry, gm.moves)
    except ValueError:
        return None

    return Build(
        species_id=species_id,
        level=level,
        fast_move=fast,
        charged_moves=tuple(charged),
        cp=get_cp_from_stats(entry.base_stats, LEAGUE_IVS, level),
    )


def instantiate(gm: GameMaster, build: Build) -> PvpPokemon:
    """Turn a Build back into a battle-ready Pokemon."""
    return gm.get_pokemon(
        build.species_id,
        build.fast_move,
        list(build.charged_moves),
        level=build.level,
        ivs=LEAGUE_IVS,
    )


def matchup_rating(attacker: PvpPokemon, defender: PvpPokemon) -> int:
    """
    The 0-1000 shield-weighted rating of `attacker` against `defender`.

    500 is an even matchup. `RosterAnalyzer.run_scenario` sweeps all nine
    shield combinations and weights them [4, 4, 1], which is the project's
    existing definition of "how good is this matchup"; this is a thin wrapper
    so every precomputed number in the repo comes from one place.
    """
    return RosterAnalyzer.run_scenario(ScenarioType.NO_BAIT, attacker, defender).rating


# ---------------------------------------------------------------------------
# Parallel rating rows
#
# One species' ratings against a fixed set of opponents is an independent unit
# of work, which is what makes this embarrassingly parallel. Workers rebuild
# the opponents once at start-up rather than shipping Pokemon across the
# process boundary on every task.
# ---------------------------------------------------------------------------

_WORKER_GM: Optional[GameMaster] = None
_WORKER_COLUMNS: List[PvpPokemon] = []


def _init_worker(columns: Sequence[Build]) -> None:
    global _WORKER_GM, _WORKER_COLUMNS
    _WORKER_GM = GameMaster()
    _WORKER_COLUMNS = [instantiate(_WORKER_GM, b) for b in columns]


def _rate_row(build: Build) -> Tuple[str, List[int]]:
    assert _WORKER_GM is not None, "worker was not initialised"
    attacker = instantiate(_WORKER_GM, build)
    return build.species_id, [matchup_rating(attacker, d) for d in _WORKER_COLUMNS]


def rating_rows(
    rows: Sequence[Build],
    columns: Sequence[Build],
    jobs: int = 0,
    progress=None,
) -> Dict[str, List[int]]:
    """
    Rate every row Pokemon against every column Pokemon.

    Returns species_id -> ratings, in column order. `jobs=1` runs in-process,
    which keeps the tests single-threaded and debuggable; anything else fans
    out across processes.
    """
    jobs = jobs or (os.cpu_count() or 1)
    done = 0

    if jobs == 1:
        _init_worker(columns)
        out = {}
        for build in rows:
            species_id, ratings = _rate_row(build)
            out[species_id] = ratings
            done += 1
            if progress:
                progress(done, len(rows))
        return out

    out = {}
    with ProcessPoolExecutor(
        max_workers=jobs, initializer=_init_worker, initargs=(list(columns),)
    ) as pool:
        for species_id, ratings in pool.map(_rate_row, rows, chunksize=4):
            out[species_id] = ratings
            done += 1
            if progress:
                progress(done, len(rows))
    return out


def _capped_by_dex(
    gm: GameMaster, ordered: Sequence[str], limit: int, per_dex: int = MAX_FORMS_PER_DEX
) -> List[str]:
    """Take the first `limit` ids, allowing at most `per_dex` forms of a species."""
    seen: Dict[int, int] = defaultdict(int)
    picked: List[str] = []
    for species_id in ordered:
        dex = gm.pokedex[species_id].dex_number
        if seen[dex] >= per_dex:
            continue
        seen[dex] += 1
        picked.append(species_id)
        if len(picked) == limit:
            break
    return picked


def select_meta(
    gm: GameMaster,
    league: str,
    size: int = DEFAULT_META_SIZE,
    jobs: int = 0,
    candidate_pool: int = CANDIDATE_POOL,
    panel_size: int = PANEL_SIZE,
    progress=None,
) -> MetaSelection:
    """Derive a league's meta. See the module docstring for the three stages."""
    cap = LEAGUE_KEYS[league].value

    builds: Dict[str, Build] = {}
    for species_id in distinct_species(gm):
        build = make_build(gm, species_id, cap)
        if build is not None:
            builds[species_id] = build

    by_stat_product = sorted(
        builds,
        key=lambda s: -stat_product(gm.pokedex[s].base_stats, LEAGUE_IVS, builds[s].level),
    )
    candidates = _capped_by_dex(gm, by_stat_product, candidate_pool)
    panel = _capped_by_dex(gm, candidates, panel_size)

    rows = rating_rows(
        [builds[s] for s in candidates],
        [builds[s] for s in panel],
        jobs=jobs,
        progress=progress,
    )
    scores = {s: sum(r) / len(r) for s, r in rows.items()}

    ranked = sorted(candidates, key=lambda s: (-scores[s], s))
    chosen = _capped_by_dex(gm, ranked, size)

    return MetaSelection(
        league=league,
        cap=cap,
        builds=[builds[s] for s in chosen],
        scores={s: scores[s] for s in chosen},
        method=(
            f"top {size} of {len(candidates)} stat-product candidates by mean "
            f"rating against a {len(panel)}-species panel"
        ),
    )


def refine_movesets(
    gm: GameMaster,
    selection: MetaSelection,
    panel_size: int = PANEL_SIZE,
    jobs: int = 0,
    progress=None,
) -> MetaSelection:
    """
    Re-pick each meta member's moveset by simulation instead of heuristic.

    These builds are the columns every other species is rated against, so a
    moveset error here biases a whole column of the matrix. Brute force is
    affordable at this size and is not affordable for the 1,100-odd species in
    the rows, which keep their heuristic movesets.
    """
    panel = list(selection.builds[:panel_size])

    candidates: List[Build] = []
    for build in selection.builds:
        entry = gm.pokedex[build.species_id]
        for fast, charged in enumerate_movesets(
            entry, gm.moves, top_fast=REFINE_TOP_FAST, top_charged=REFINE_TOP_CHARGED
        ):
            candidates.append(
                Build(
                    species_id=build.species_id,
                    level=build.level,
                    fast_move=fast,
                    charged_moves=tuple(charged),
                    cp=build.cp,
                )
            )

    # rating_rows keys on species_id, which is not unique across movesets, so
    # rate the variants positionally instead.
    ratings = _rate_variants(candidates, panel, jobs=jobs, progress=progress)

    best_for: Dict[str, Tuple[float, Build]] = {}
    for build, score in zip(candidates, ratings, strict=True):
        current = best_for.get(build.species_id)
        if current is None or score > current[0]:
            best_for[build.species_id] = (score, build)

    refined = [best_for[b.species_id][1] for b in selection.builds]
    return MetaSelection(
        league=selection.league,
        cap=selection.cap,
        builds=refined,
        scores=selection.scores,
        method=selection.method + f"; movesets re-picked by simulation vs the top {len(panel)}",
    )


def _rate_variants(
    variants: Sequence[Build], columns: Sequence[Build], jobs: int = 0, progress=None
) -> List[float]:
    """Mean rating of each build against the columns, in input order."""
    jobs = jobs or (os.cpu_count() or 1)
    done = 0
    out: List[float] = []

    if jobs == 1:
        _init_worker(columns)
        for build in variants:
            _, ratings = _rate_row(build)
            out.append(sum(ratings) / len(ratings))
            done += 1
            if progress:
                progress(done, len(variants))
        return out

    with ProcessPoolExecutor(
        max_workers=jobs, initializer=_init_worker, initargs=(list(columns),)
    ) as pool:
        for _, ratings in pool.map(_rate_row, variants, chunksize=8):
            out.append(sum(ratings) / len(ratings))
            done += 1
            if progress:
                progress(done, len(variants))
    return out


def build_league(
    gm: GameMaster,
    league: str,
    size: int = DEFAULT_META_SIZE,
    jobs: int = 0,
    refine: bool = True,
    candidate_pool: int = CANDIDATE_POOL,
    panel_size: int = PANEL_SIZE,
    progress=None,
) -> dict:
    """
    Everything the website needs for one league, as a JSON-ready dict.

    `ratings[species_id][i]` is that species' 0-1000 rating against
    `meta[i]`. Rows cover every battle-distinct species, so the team builder
    can answer for any pick, not only for meta picks; `aliases` maps the
    cosmetic forms that were folded away back onto their representative.
    """
    if league not in LEAGUE_KEYS:
        raise ValueError(f"unknown league {league!r}; expected one of {sorted(LEAGUE_KEYS)}")

    def step(label: str):
        return (lambda done, total: progress(label, done, total)) if progress else None

    selection = select_meta(
        gm,
        league,
        size=size,
        jobs=jobs,
        candidate_pool=candidate_pool,
        panel_size=panel_size,
        progress=step("select"),
    )
    if refine:
        selection = refine_movesets(
            gm, selection, panel_size=panel_size, jobs=jobs, progress=step("refine")
        )

    # A meta member must use the same build in its own row as it does as a
    # column, or its mirror match is not a mirror and reads as a losing
    # matchup against itself.
    refined = {b.species_id: b for b in selection.builds}
    row_builds = [
        refined.get(b.species_id, b)
        for b in (make_build(gm, s, selection.cap) for s in distinct_species(gm))
        if b is not None
    ]
    rows = rating_rows(row_builds, selection.builds, jobs=jobs, progress=step("rate"))

    # A representative with no usable fast move (its pool holds only Struggle)
    # produces no row, so the forms pointing at it would dangle.
    rated = {b.species_id for b in row_builds}
    aliases = {
        member: representative
        for representative, members in clone_groups(gm).items()
        for member in members
        if member != representative and representative in rated
    }

    return {
        "league": league,
        "cap": selection.cap,
        "assumptions": {
            "ivs": LEAGUE_IVS.to_dict(),
            "shield_weights": [4, 4, 1],
            "energy_budget": ENERGY_BUDGET,
            "meta_selection": selection.method,
            "note": (
                "Ratings are 0-1000 from RosterAnalyzer.run_scenario; 500 is even. "
                "Every build uses the IV spread above at the highest level under the "
                "cap. Meta movesets are simulated; row movesets are heuristic."
            ),
        },
        "meta": [
            {
                "id": b.species_id,
                "cp": b.cp,
                "level": b.level,
                "fast": b.fast_move,
                "charged": list(b.charged_moves),
                "score": round(selection.scores.get(b.species_id, 0.0), 1),
            }
            for b in selection.builds
        ],
        "builds": {
            b.species_id: {
                "cp": b.cp,
                "level": b.level,
                "fast": b.fast_move,
                "charged": list(b.charged_moves),
            }
            for b in row_builds
        },
        "ratings": {b.species_id: rows[b.species_id] for b in row_builds},
        "aliases": aliases,
    }


def matchups_filename(league: str) -> str:
    """Name of the precomputed file for a league, alongside the derived dataset."""
    return f"matchups.{league}.json"
