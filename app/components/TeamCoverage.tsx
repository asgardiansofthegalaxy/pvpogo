"use client";

import SpeciesAvatar from "@/app/components/SpeciesAvatar";
import {
  describeRating,
  speciesName,
  type CoverageEntry,
  type TeamCoverage,
} from "@/app/lib/matchups";
import { titleCase, type Species } from "@/app/lib/pokemon";

interface Props {
  coverage: TeamCoverage | null;
  speciesById: Map<string, Species>;
  /** Members picked so far, so a partial team can say what it is. */
  picked: number;
  teamSize: number;
  /** How many gaps to list before summarising the rest. */
  limit?: number;
}

/**
 * What the team as a whole answers, and what beats all of it.
 *
 * The per-pick panel says how one Pokémon fares. This is the question a team
 * builder exists for: given these picks, which meta threats has the team got
 * nothing for. It is a lookup over the precomputed matrix, so it updates as
 * fast as the user can click.
 */
export default function TeamCoveragePanel({
  coverage,
  speciesById,
  picked,
  teamSize,
  limit = 5,
}: Props) {
  if (picked === 0) {
    return (
      <section
        aria-label="Team coverage"
        className="rounded-2xl border border-dashed border-teal-400/25 px-4 py-5"
      >
        <h2 className="text-sm font-semibold text-teal-50">Team coverage</h2>
        <p className="mt-1 text-xs leading-relaxed text-teal-300/70">
          Pick a Pokémon and this shows which meta threats your team has an
          answer to — and which beat all of it.
        </p>
      </section>
    );
  }

  if (!coverage) {
    return (
      <section
        aria-label="Team coverage"
        aria-busy="true"
        className="h-32 animate-pulse rounded-2xl bg-teal-950/40 ring-1 ring-teal-400/10"
      >
        <span className="sr-only">Loading team coverage</span>
      </section>
    );
  }

  const { score, gaps, answered, total } = coverage;
  const partial = picked < teamSize;

  return (
    <section
      aria-label="Team coverage"
      className="rounded-2xl bg-teal-950/40 p-4 ring-1 ring-teal-400/15"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold text-teal-50">Team coverage</h2>
        <span
          className="shrink-0 text-[0.65rem] text-teal-400/70"
          title="The best rating any member manages against each meta pick, averaged over the meta. 500 is even."
        >
          best answer{" "}
          <span
            className={`font-semibold tabular-nums ${
              score >= 500 ? "text-emerald-300" : "text-amber-300"
            }`}
          >
            {score}
          </span>
        </span>
      </div>

      <p className="mt-1 text-xs text-teal-300/80">
        <span className="font-semibold tabular-nums text-teal-100">
          {answered}
        </span>{" "}
        of {total} meta picks answered
        {partial && (
          <span className="text-teal-400/60">
            {" "}
            · {picked} of {teamSize} picked
          </span>
        )}
      </p>

      {gaps.length === 0 ? (
        <p className="mt-3 rounded-lg bg-emerald-400/10 px-3 py-2 text-xs leading-relaxed text-emerald-200/90">
          Nothing in the meta beats every member. Each pick still has its own
          bad matchups — the team covers them.
        </p>
      ) : (
        <>
          <p className="mb-1.5 mt-3 text-[0.6rem] uppercase tracking-wide text-teal-400/60">
            Beats your whole team
          </p>
          <ul className="space-y-1">
            {gaps.slice(0, limit).map((gap) => (
              <GapRow key={gap.opponent.id} gap={gap} speciesById={speciesById} />
            ))}
          </ul>
          {gaps.length > limit && (
            <p className="mt-1.5 text-[0.65rem] text-teal-400/60">
              and {gaps.length - limit} more
            </p>
          )}
        </>
      )}

      <p className="mt-3 border-t border-teal-400/10 pt-2 text-[0.6rem] leading-relaxed text-teal-400/50">
        One-on-one ratings, so this asks whether anything on the team beats a
        pick — not how a real 3v3 with switching would go.
      </p>
    </section>
  );
}

function GapRow({
  gap,
  speciesById,
}: {
  gap: CoverageEntry;
  speciesById: Map<string, Species>;
}) {
  const name = speciesName(speciesById, gap.opponent.id);
  const closest = speciesName(speciesById, gap.answeredBy);
  const types = speciesById.get(gap.opponent.id)?.types ?? [];

  const mirrorNote = gap.onTeam
    ? ` You run ${name} too, but a mirror is a coin flip, so it does not count as the team's answer.`
    : "";

  return (
    <li
      className="flex items-center gap-2 rounded-md bg-rose-400/5 px-2 py-1"
      title={`${describeRating(gap.best)} — ${closest} is the team's best answer at ${gap.best}/1000${
        types.length ? ` against ${name} (${types.map(titleCase).join(" / ")})` : ""
      }.${mirrorNote}`}
    >
      <SpeciesAvatar name={name} types={types} size="sm" />
      <span className="min-w-0 flex-1">
        <span className="flex items-baseline gap-1.5">
          <span className="truncate text-[0.7rem] text-teal-50">{name}</span>
          {gap.onTeam && (
            <span className="shrink-0 rounded bg-teal-400/15 px-1 py-px text-[0.55rem] uppercase tracking-wide text-teal-300/80">
              mirror
            </span>
          )}
        </span>
        <span className="block truncate text-[0.6rem] text-teal-400/60">
          best: {closest}
        </span>
      </span>
      <span className="shrink-0 text-[0.7rem] font-semibold tabular-nums text-rose-200">
        {gap.best}
      </span>
    </li>
  );
}
