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

const cache: Partial<Record<LeagueKey, Promise<MatchupData>>> = {};

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

/**
 * The id a species' ratings live under.
 *
 * Nineteen Vivillon patterns battle identically, so the engine simulates one
 * and records the rest as aliases.
 */
export function ratedId(data: MatchupData, speciesId: string): string {
  return data.aliases[speciesId] ?? speciesId;
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
    build: data.builds[id] ?? null,
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
