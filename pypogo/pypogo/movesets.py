"""
Choosing a species' battle moveset without simulating every option.

The dataset lists a species' legal moves in the order the export happens to
carry them, which is not a ranking: Azumarill's first fast move is Rock Smash,
which no PvP player runs. Anything that builds a Pokemon without naming moves
inherits that order, so every analysis built on default movesets is measuring
the wrong Pokemon.

Brute-forcing the choice is possible -- simulate a species' movesets against a
panel and keep the winner -- but it costs about a second per species, which is
affordable for a hundred meta picks and not for all 1,279. This module scores
moves directly instead.

The two scores are deliberately dimensional rather than tuned:

* A charged move is worth its damage per energy. Energy that never gets spent
  is wasted, though, and a move can only be thrown in whole multiples of its
  cost, so the leftover -- half the cost, on average -- is subtracted from the
  energy a battle generates. That is what stops a 75-energy nuke from
  outranking a 35-energy move it never gets to throw twice.
* A fast move is worth the damage it deals directly plus the damage its energy
  buys, valued at the species' own best charged-move damage per energy. That
  is a conversion factor the species supplies, not a fitted weight, and it is
  what lets Lock On -- 1 power, 12 energy -- outrank a hard-hitting fast move
  on Registeel.

`tests/test_movesets.py` checks these against brute-force simulation and pins
the resulting error, so a future change has to argue with a number.
"""

from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from .constants import STAB_BONUS
from .moves import Move
from .pokedex import PokedexEntry

#: Energy a Pokemon generates over a 1v1, in the units charged moves cost.
#: Only the ratio to a move's cost matters, and the ranking is flat for
#: anything from ~150 to ~600 (see tests/test_movesets.py), so this is a
#: plateau value rather than a fitted one: a fast move earning ~3.5 energy a
#: turn over a battle that lasts a minute or so lands in the same range.
ENERGY_BUDGET = 250.0


def _stab(move: Move, entry: PokedexEntry) -> float:
    """Same-type attack bonus, the one damage term that depends on the user."""
    return STAB_BONUS if move.move_type in entry.types else 1.0


def charged_move_score(move: Move, entry: PokedexEntry) -> float:
    """
    How much damage this charged move buys with a battle's worth of energy.

    Damage per energy, applied to the energy actually spendable on a move of
    this cost. `max(..., 1.0)` keeps a move that costs more than the whole
    budget ranked by its efficiency rather than collapsing to zero.
    """
    damage_per_energy = move.power * _stab(move, entry) / move.energy
    spendable = max(ENERGY_BUDGET - move.energy / 2, 1.0)
    return damage_per_energy * spendable


def fast_move_score(move: Move, entry: PokedexEntry, best_damage_per_energy: float) -> float:
    """
    Damage a fast move produces per turn, counting the charged damage it funds.

    `best_damage_per_energy` converts energy into damage at the rate this
    species' best charged move actually achieves, so a species with a cheap,
    efficient charged move values energy generation more than one without.
    """
    damage_per_turn = move.power * _stab(move, entry) / move.cooldown_turns
    energy_per_turn = move.energy_gain / move.cooldown_turns
    return damage_per_turn + energy_per_turn * best_damage_per_energy


def _usable_moves(
    entry: PokedexEntry, moves: Dict[str, Move]
) -> Tuple[List[Move], List[Move]]:
    """
    Split a species' declared pools into battle-usable fast and charged moves.

    The export lists Struggle under quickMoves for a few never-implemented
    species, so the declared pool is filtered by what the move actually is
    rather than trusted outright.
    """
    fast = [moves[mid] for mid in entry.fast_moves if mid in moves and moves[mid].is_fast]
    charged = [
        moves[mid] for mid in entry.charged_moves if mid in moves and not moves[mid].is_fast
    ]
    return fast, charged


def rank_charged_moves(entry: PokedexEntry, moves: Dict[str, Move]) -> List[Move]:
    """This species' charged moves, best first. Ties break on move_id."""
    _, charged = _usable_moves(entry, moves)
    return sorted(charged, key=lambda m: (-charged_move_score(m, entry), m.move_id))


def rank_fast_moves(entry: PokedexEntry, moves: Dict[str, Move]) -> List[Move]:
    """This species' fast moves, best first. Ties break on move_id."""
    fast, charged = _usable_moves(entry, moves)
    if not charged:
        return sorted(fast, key=lambda m: m.move_id)

    best_dpe = max(m.power * _stab(m, entry) / m.energy for m in charged)
    return sorted(fast, key=lambda m: (-fast_move_score(m, entry, best_dpe), m.move_id))


def best_moveset(entry: PokedexEntry, moves: Dict[str, Move]) -> Tuple[str, List[str]]:
    """
    The moveset to build this species with: one fast move and up to two charged.

    Returns move ids, in the shape `GameMaster.get_pokemon` takes. Raises
    ValueError for a species with no usable pool, matching what `get_pokemon`
    does with the same species, so callers have one failure mode to handle.
    """
    fast, charged = _usable_moves(entry, moves)
    if not fast or not charged:
        raise ValueError(
            f"{entry.species_id!r} declares no usable moveset in the dataset and "
            "cannot be built."
        )

    ranked_fast = rank_fast_moves(entry, moves)
    ranked_charged = rank_charged_moves(entry, moves)
    return ranked_fast[0].move_id, [m.move_id for m in ranked_charged[:2]]


def enumerate_movesets(
    entry: PokedexEntry,
    moves: Dict[str, Move],
    top_fast: Optional[int] = None,
    top_charged: Optional[int] = None,
) -> List[Tuple[str, List[str]]]:
    """
    Every legal (fast move, charged pair) this species can run.

    Used by the tests to establish what the best moveset actually is, and by
    the meta builder to refine the picks it can afford to simulate.

    `top_fast` and `top_charged` narrow the search to the best moves by the
    scores above, which turns an exhaustive search into a local one around the
    heuristic's pick. That matters for exactly one species: Mew declares 4,200
    legal movesets where the next-widest pool has 84, enough to cost more than
    the rest of a league's build put together.
    """
    fast_ranked = rank_fast_moves(entry, moves)
    charged_ranked = rank_charged_moves(entry, moves)
    fast = fast_ranked[:top_fast] if top_fast else fast_ranked
    charged = charged_ranked[:top_charged] if top_charged else charged_ranked
    ids = sorted(m.move_id for m in charged)
    pairs: List[List[str]] = [list(p) for p in combinations(ids, 2)] or [[i] for i in ids]
    return [(f.move_id, pair) for f in sorted(fast, key=lambda m: m.move_id) for pair in pairs]


def moveset_names(fast: str, charged: Sequence[str], moves: Dict[str, Move]) -> str:
    """Human-readable moveset, for build logs and test failure messages."""
    label = moves[fast].name.replace(" Fast", "") if fast in moves else fast
    rest = ", ".join(moves[c].name if c in moves else c for c in charged)
    return f"{label} / {rest}"
