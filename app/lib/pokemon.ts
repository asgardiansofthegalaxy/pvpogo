/**
 * Frontend data layer over the engine's exported dataset.
 *
 * The Python engine is the source of truth for both the data and the formulas;
 * scripts/build-web-data.mjs exports the data, and the maths below mirrors
 * pypogo/stats.py exactly. Anything that disagrees with the engine is a bug
 * here, not there.
 */

export interface Stats {
  atk: number;
  def: number;
  sta: number;
}

export interface Species {
  id: string;
  name: string;
  dex: number;
  types: string[];
  stats: Stats;
  fastMoves: string[];
  chargedMoves: string[];
}

export interface MoveBuff {
  chance: number;
  atk_buff_self: number;
  def_buff_self: number;
  atk_buff_opponent: number;
  def_buff_opponent: number;
}

export interface Move {
  id: string;
  name: string;
  type: string;
  fast: boolean;
  power: number;
  energy: number;
  energyGain: number;
  /** Duration in 500ms battle turns. */
  turns: number;
  buff: MoveBuff | null;
}

export type MoveTable = Record<string, Move>;

/** GO Battle League CP caps. Master is uncapped; 10000 stands in for "no cap". */
export const LEAGUES = {
  great: { name: "Great League", short: "Great", cap: 1500 },
  ultra: { name: "Ultra League", short: "Ultra", cap: 2500 },
  master: { name: "Master League", short: "Master", cap: 10000 },
} as const;

export type LeagueKey = keyof typeof LEAGUES;

/** A Great League team is three Pokemon, as in GO Battle League. */
export const TEAM_SIZE = 3;

export const MAX_IV = 15;
export const MAX_LEVEL = 50;

export interface LoadedData {
  species: Species[];
  moves: MoveTable;
  cpMultipliers: number[];
}

let cache: Promise<LoadedData> | null = null;

/** Fetch the exported dataset once per page load. ~49 KB gzipped in total. */
export function loadData(): Promise<LoadedData> {
  if (!cache) {
    cache = Promise.all([
      fetch("/data/species.json").then((r) => r.json() as Promise<Species[]>),
      fetch("/data/moves.json").then((r) => r.json() as Promise<MoveTable>),
      fetch("/data/cp-multipliers.json").then((r) => r.json() as Promise<number[]>),
    ]).then(([species, moves, cpMultipliers]) => ({ species, moves, cpMultipliers }));
  }
  return cache;
}

/** Mirrors pypogo/stats.py::get_cp_from_stats. */
export function calculateCp(
  base: Stats,
  ivs: Stats,
  level: number,
  cpMultipliers: number[]
): number {
  const cpm = cpMultipliers[Math.floor((level - 1) * 2)];
  if (cpm === undefined) return 0;

  const cp = Math.floor(
    0.1 *
      cpm ** 2 *
      (base.atk + ivs.atk) *
      Math.sqrt((base.def + ivs.def) * (base.sta + ivs.sta))
  );
  return Math.max(cp, 10);
}

/** Mirrors the effective-stat derivation in pypogo/pokemon.py. */
export function effectiveStats(
  base: Stats,
  ivs: Stats,
  level: number,
  cpMultipliers: number[]
): Stats {
  const cpm = cpMultipliers[Math.floor((level - 1) * 2)] ?? 0;
  return {
    atk: cpm * (base.atk + ivs.atk),
    def: cpm * (base.def + ivs.def),
    sta: Math.max(Math.floor(cpm * (base.sta + ivs.sta)), 10),
  };
}

/**
 * Stat product — the standard bulk-vs-attack measure PvP players rank by.
 * Scaled down so it reads as a handful of thousands rather than millions.
 */
export function statProduct(stats: Stats): number {
  return Math.round((stats.atk * stats.def * stats.sta) / 1000);
}

/**
 * Highest half-level that keeps this Pokemon under a league's CP cap.
 *
 * The cap, not raw level, is what makes a Great League pick viable, so the
 * builder defaults every pick to it. Returns null when even level 1 is over.
 */
export function maxLevelUnderCap(
  base: Stats,
  ivs: Stats,
  cap: number,
  cpMultipliers: number[]
): number | null {
  let best: number | null = null;
  for (let level = 1; level <= MAX_LEVEL; level += 0.5) {
    if (calculateCp(base, ivs, level, cpMultipliers) <= cap) best = level;
    else break;
  }
  return best;
}

export const ALL_TYPES = [
  "normal", "fire", "water", "electric", "grass", "ice",
  "fighting", "poison", "ground", "flying", "psychic", "bug",
  "rock", "ghost", "dragon", "dark", "steel", "fairy",
] as const;

/** Dataset stores types lowercase; the UI's colour maps are capitalised. */
export function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
