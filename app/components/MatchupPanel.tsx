"use client";

import {
  buildMatches,
  describeRating,
  speciesName,
  spreadMatches,
  type Matchup,
  type SpeciesMatchups,
} from "@/app/lib/matchups";
import {
  titleCase,
  type MoveTable,
  type Species,
  type Stats,
} from "@/app/lib/pokemon";

interface Props {
  matchups: SpeciesMatchups;
  speciesById: Map<string, Species>;
  moves: MoveTable;
  fastMoveId: string;
  chargedMoveIds: string[];
  ivs: Stats;
  level: number;
  /** How many of each side to show. The data file carries six. */
  limit?: number;
}

/**
 * A pick's best and worst matchups against the league meta.
 *
 * The numbers come from `public/data/matchups.<league>.json`, simulated
 * offline. They describe one specific build of this species, so when the user
 * has re-specced their pick the panel says so rather than quietly showing
 * numbers for a different Pokemon.
 */
export default function MatchupPanel({
  matchups,
  speciesById,
  moves,
  fastMoveId,
  chargedMoveIds,
  ivs,
  level,
  limit = 3,
}: Props) {
  const { build, score, best, worst, assumedIvs } = matchups;
  const matchesMoves = buildMatches(build, fastMoveId, chargedMoveIds);
  const matchesSpread = spreadMatches(build, assumedIvs, ivs, level);

  return (
    <section className="mt-4 border-t border-teal-400/10 pt-3">
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <h4 className="text-[0.65rem] font-semibold uppercase tracking-wide text-teal-300/80">
          Against the meta
        </h4>
        <span
          className="shrink-0 text-[0.65rem] text-teal-400/70"
          title="Mean battle rating against every meta pick. 500 is an even matchup."
        >
          avg{" "}
          <span
            className={`font-semibold tabular-nums ${
              score >= 500 ? "text-emerald-300" : "text-amber-300"
            }`}
          >
            {score}
          </span>
        </span>
      </div>

      <div className="grid gap-x-4 gap-y-3 sm:grid-cols-2">
        <MatchupList
          label="Beats"
          rows={best.slice(0, limit)}
          speciesById={speciesById}
        />
        <MatchupList
          label="Loses to"
          rows={worst.slice(0, limit)}
          speciesById={speciesById}
        />
      </div>

      {build && !(matchesMoves && matchesSpread) && (
        <div className="mt-2.5 space-y-1 rounded-lg bg-amber-400/10 px-2.5 py-1.5 text-[0.65rem] leading-relaxed text-amber-200/90">
          {!matchesMoves && (
            <p>
              Simulated with{" "}
              <span className="font-medium">{moveLabel(moves, build.fast)}</span>{" "}
              and{" "}
              <span className="font-medium">
                {build.charged.map((id) => moveLabel(moves, id)).join(" + ")}
              </span>
              , not the moves you picked.
            </p>
          )}
          {!matchesSpread && (
            <p>
              Simulated at{" "}
              <span className="font-medium">
                {assumedIvs.atk}/{assumedIvs.def}/{assumedIvs.sta}
              </span>
              , level <span className="font-medium">{build.level}</span> — not
              your spread.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

function MatchupList({
  label,
  rows,
  speciesById,
}: {
  label: string;
  rows: Matchup[];
  speciesById: Map<string, Species>;
}) {
  return (
    <div className="min-w-0">
      <p className="mb-1 text-[0.6rem] uppercase tracking-wide text-teal-400/60">
        {label}
      </p>
      <ul className="space-y-1">
        {rows.length === 0 && (
          <li className="text-[0.65rem] text-teal-400/50">No data</li>
        )}
        {rows.map(({ opponent, rating }) => (
          <MatchupRow
            key={opponent.id}
            name={speciesName(speciesById, opponent.id)}
            types={speciesById.get(opponent.id)?.types ?? []}
            rating={rating}
          />
        ))}
      </ul>
    </div>
  );
}

function MatchupRow({
  name,
  types,
  rating,
}: {
  name: string;
  types: readonly string[];
  rating: number;
}) {
  const winning = rating >= 500;

  return (
    <li
      className="relative isolate overflow-hidden rounded-md bg-teal-400/5"
      title={`${describeRating(rating)} — ${rating}/1000 against ${name}${
        types.length ? ` (${types.map(titleCase).join(" / ")})` : ""
      }`}
    >
      {/* The bar is the rating: full width would be a 1000 rating. */}
      <span
        aria-hidden
        className={`absolute inset-y-0 left-0 -z-10 ${
          winning ? "bg-emerald-400/20" : "bg-rose-400/20"
        }`}
        style={{ width: `${Math.max(2, Math.min(100, rating / 10))}%` }}
      />
      <div className="flex items-baseline justify-between gap-2 px-2 py-1">
        <span className="truncate text-[0.7rem] text-teal-50">{name}</span>
        <span
          className={`shrink-0 text-[0.7rem] font-semibold tabular-nums ${
            winning ? "text-emerald-200" : "text-rose-200"
          }`}
        >
          {rating}
        </span>
      </div>
    </li>
  );
}

function moveLabel(moves: MoveTable, id: string): string {
  return moves[id]?.name ?? id;
}
