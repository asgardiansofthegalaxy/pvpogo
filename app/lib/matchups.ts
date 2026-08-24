/**
 * Precomputed matchup data.
 *
 * The Python engine simulates every species against its league's meta offline
 * (pypogo/scripts/build_matchups.py) and the result ships as static JSON, so
 * the browser answers "how does this pick fare" by lookup rather than by
 * calling a simulator. Nothing here computes a battle; it only reads what the
 * engine already decided.
 *
 * Ratings are 0-1000, where 500 is an even matchup: half the score is damage
 * dealt, half is HP retained, averaged over all nine shield combinations.
 */

import type { LeagueKey, Species } from "@/app/lib/pokemon";

/** The rating an even matchup produces: half the damage, half the HP. */
export const EVEN_RATING = 500;

export interface MetaEntry {
  id: string;
  cp: number;
  level: number;
  fast: string;
  charged: string[];
}

export interface SimulatedBuild {
  cp: number;
  level: number;
  fast: string;
  charged: string[];
}

/** `[index into meta, rating]`, which is how the file keeps rows small. */
export type RatedMatchup = readonly [number, number];

export interface MatchupData {
  league: string;
  cap: number;
  assumptions: {
    ivs: { attack: number; defense: number; stamina: number };
    shield_weights: number[];
    energy_budget: number;
    meta_selection: string;
    note: string;
  };
  meta: MetaEntry[];
  builds: Record<string, SimulatedBuild>;
  best: Record<string, RatedMatchup[]>;
  worst: Record<string, RatedMatchup[]>;
  score: Record<string, number>;
  /** Cosmetic forms folded onto the entry that is mechanically identical. */
  aliases: Record<string, string>;
}

export interface Matchup {
  opponent: MetaEntry;
  rating: number;
}

export interface SpeciesMatchups {
  /** The id the ratings were actually computed for, after alias resolution. */
  ratedAs: string;
  build: SimulatedBuild | null;
  score: number;
  best: Matchup[];
  worst: Matchup[];
}

/**
 * Every species' full row against the league meta.
 *
 * Shipped separately from the summary because it is the larger half of the
 * data by far and only the team-level analysis needs it -- the builder fetches
 * it once there is a team to analyse rather than on page load.
 */
export interface MatchupRows {
  league: string;
  /** Meta ids in column order, so a stale file cannot silently misalign. */
  meta: string[];
  ratings: Record<string, number[]>;
}

const cache: Partial<Record<LeagueKey, Promise<MatchupData>>> = {};
const rowCache: Partial<Record<LeagueKey, Promise<MatchupRows>>> = {};

/** Fetch a league's matchup file once per page load. */
export function loadMatchups(league: LeagueKey): Promise<MatchupData> {
  let pending = cache[league];
  if (!pending) {
    pending = fetch(`/data/matchups.${league}.json`).then(
      (r) => r.json() as Promise<MatchupData>
    );
    cache[league] = pending;
  }
  return pending;
}

/** Fetch a league's full matchup rows once per page load. */
export function loadMatchupRows(league: LeagueKey): Promise<MatchupRows> {
  let pending = rowCache[league];
  if (!pending) {
    pending = fetch(`/data/matchups.${league}.rows.json`).then(
      (r) => r.json() as Promise<MatchupRows>
    );
    rowCache[league] = pending;
  }
  return pending;
}

/**
 * The id a species' ratings live under.
 *
 * Nineteen Vivillon patterns battle identically, so the engine simulates one
 * and records the rest as aliases.
 */
export function ratedId(data: MatchupData, speciesId: string): string {
  return data.aliases[speciesId] ?? speciesId;
}

/**
 * The build a species' ratings were simulated with, or null if it has none.
 *
 * Every species the engine can build has one: the meta's are brute-forced,
 * the rest come from the same ranking that orders the exported move pools.
 * It is the best moveset this project knows for the league, which makes it
 * the right default for a fresh pick as well as the caption on the numbers.
 */
export function buildFor(
  data: MatchupData,
  speciesId: string
): SimulatedBuild | null {
  return data.builds[ratedId(data, speciesId)] ?? null;
}

function hydrate(data: MatchupData, rows: RatedMatchup[] | undefined): Matchup[] {
  if (!rows) return [];
  return rows
    .filter(([index]) => data.meta[index] !== undefined)
    .map(([index, rating]) => ({ opponent: data.meta[index], rating }));
}

/**
 * A species' best and worst matchups against the league meta.
 *
 * Returns null for a species the engine could not build -- the handful with no
 * base stats or no declared moveset.
 */
export function matchupsFor(
  data: MatchupData,
  speciesId: string
): SpeciesMatchups | null {
  const id = ratedId(data, speciesId);
  if (!data.best[id]) return null;

  return {
    ratedAs: id,
    build: buildFor(data, id),
    score: data.score[id] ?? 0,
    best: hydrate(data, data.best[id]),
    worst: hydrate(data, data.worst[id]),
  };
}

/**
 * Whether a user's build differs from the one the ratings were simulated with.
 *
 * The matrix fixes a moveset and level per species, so a pick the user has
 * re-specced is not the Pokemon these numbers describe. Saying so is cheaper
 * than pretending otherwise.
 */
export function buildMatches(
  build: SimulatedBuild | null,
  fastMoveId: string,
  chargedMoveIds: string[]
): boolean {
  if (!build) return true;
  const chosen = [...chargedMoveIds].sort().join(",");
  const simulated = [...build.charged].sort().join(",");
  return build.fast === fastMoveId && chosen === simulated;
}

/** A meta pick, and the best answer the team has to it. */
export interface CoverageEntry {
  opponent: MetaEntry;
  /** The best rating any team member manages against it. */
  best: number;
  /** Which member holds that best answer, as a species id. */
  answeredBy: string;
  /**
   * Whether the team runs this pick too. The mirror is excluded from the
   * answer, so such a row means "your other picks lose to it" -- worth
   * flagging, since relying on a coin-flip mirror is not coverage.
   */
  onTeam: boolean;
}

export interface TeamCoverage {
  /**
   * The team's best answer against each meta pick, averaged over the meta.
   * 500 is even. Higher than a single pick's mean by construction -- it is a
   * mean of maxima, and it assumes you get to bring the right member.
   */
  score: number;
  /** Meta picks no member beats, worst answer first. */
  gaps: CoverageEntry[];
  /** Meta picks at least one member beats. */
  answered: number;
  total: number;
  /** Members with no row in the matrix, left out of the calculation. */
  unrated: string[];
}

/**
 * Which meta picks the team has an answer to, and which beat all of it.
 *
 * This is a lookup, not a simulation: `rows` already holds every 1v1 rating,
 * so the team-level answer is a scan down each meta column for the member that
 * does best against it. A column where nobody clears 500 is a coverage gap --
 * the thing a team builder exists to surface.
 *
 * Being 1v1, it says nothing about switching or shield pressure across a real
 * 3v3. It answers "does anything on this team beat that", which is the
 * question worth asking while picking.
 *
 * Returns null if the two files disagree about the meta, since lining a row up
 * against the wrong opponent would be worse than showing nothing.
 */
export function teamCoverage(
  data: MatchupData,
  rows: MatchupRows,
  speciesIds: string[]
): TeamCoverage | null {
  if (rows.meta.length !== data.meta.length) return null;
  if (rows.meta.some((id, i) => data.meta[i]?.id !== id)) return null;

  const rated: { id: string; ratings: number[] }[] = [];
  const unrated: string[] = [];

  for (const speciesId of speciesIds) {
    const ratings = rows.ratings[ratedId(data, speciesId)];
    if (ratings?.length === data.meta.length) rated.push({ id: speciesId, ratings });
    else unrated.push(speciesId);
  }

  if (rated.length === 0) return null;

  const gaps: CoverageEntry[] = [];
  let total = 0;

  data.meta.forEach((opponent, column) => {
    // A mirror rates ~500 by construction and lands within ~100 either way, so
    // counting a member as its own answer would decide these rows on noise.
    // The rest of the team is what gets measured instead.
    const answers = rated.filter(({ id }) => ratedId(data, id) !== opponent.id);
    const onTeam = answers.length !== rated.length;
    if (answers.length === 0) return;

    const strongest = answers.reduce((a, b) =>
      b.ratings[column] > a.ratings[column] ? b : a
    );
    const best = strongest.ratings[column];

    total += best;
    if (best < EVEN_RATING) {
      gaps.push({ opponent, best, answeredBy: strongest.id, onTeam });
    }
  });

  const columns = data.meta.length;
  gaps.sort((a, b) => a.best - b.best);

  return {
    score: Math.round(total / columns),
    gaps,
    answered: columns - gaps.length,
    total: columns,
    unrated,
  };
}

/** How a rating reads in words. 500 is even by construction. */
export function describeRating(rating: number): string {
  if (rating >= 750) return "Dominant";
  if (rating >= 600) return "Favoured";
  if (rating >= 500) return "Slight edge";
  if (rating >= 400) return "Slight loss";
  if (rating >= 250) return "Unfavoured";
  return "Overwhelmed";
}

/** Name for a meta entry, falling back to the id when the species is unknown. */
export function speciesName(
  speciesById: Map<string, Species>,
  id: string
): string {
  return speciesById.get(id)?.name ?? id;
}
