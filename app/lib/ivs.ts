/**
 * Best IVs under a CP cap.
 *
 * A CP cap is what makes IV choice interesting: CP weights attack quadratically
 * while stat product does not, so under a cap the strongest spread is usually
 * the one with the *lowest* attack IV, levelled higher to spend the headroom on
 * bulk. That is counterintuitive enough to be worth computing rather than
 * guessing at.
 *
 * All 4,096 spreads at their own best level is ~30ms in the browser, so this
 * runs on demand rather than shipping as another precomputed file. The formulas
 * come from `app/lib/pokemon.ts`, which mirrors the engine's.
 *
 * Ranked by stat product, matching `meta.py::stat_product` and the figure the
 * team slot already displays. `StatsRanker` in the engine ranks by the *sum* of
 * effective stats instead; the two mostly agree at the top -- Registeel is the
 * widest gap of the ones measured, at 4 stat product in 2,405 -- but product is
 * the measure the rest of this project uses.
 */

import {
  MAX_IV,
  calculateCp,
  effectiveStats,
  maxLevelUnderCap,
  statProduct,
  type Stats,
} from "@/app/lib/pokemon";

export interface RankedSpread {
  ivs: Stats;
  /** The highest level this spread reaches under the cap. */
  level: number;
  cp: number;
  /** Scaled the same way the team slot displays it. */
  statProduct: number;
}

export interface IvRanking {
  /** Every spread that can make the cap, best first. */
  spreads: RankedSpread[];
  /** 1-based rank, keyed by `spreadKey`. */
  ranks: Map<string, number>;
}

/** How a spread is keyed for rank lookup. Atk/def/sta, the order the UI shows. */
export function spreadKey(ivs: Stats): string {
  return `${ivs.atk}/${ivs.def}/${ivs.sta}`;
}

/**
 * Every IV spread ranked by the stat product it reaches under the cap.
 *
 * Spreads that are over the cap even at level 1 are absent rather than ranked
 * last: they are not builds, so counting them would inflate every rank.
 */
export function rankIvs(
  base: Stats,
  cap: number,
  cpMultipliers: number[]
): IvRanking {
  const scored: { spread: RankedSpread; product: number }[] = [];

  for (let atk = 0; atk <= MAX_IV; atk++) {
    for (let def = 0; def <= MAX_IV; def++) {
      for (let sta = 0; sta <= MAX_IV; sta++) {
        const ivs = { atk, def, sta };
        const level = maxLevelUnderCap(base, ivs, cap, cpMultipliers);
        if (level === null) continue;

        const effective = effectiveStats(base, ivs, level, cpMultipliers);
        scored.push({
          // Unrounded, so ordering is not decided by display rounding.
          product: effective.atk * effective.def * effective.sta,
          spread: {
            ivs,
            level,
            cp: calculateCp(base, ivs, level, cpMultipliers),
            statProduct: statProduct(effective),
          },
        });
      }
    }
  }

  scored.sort(
    (a, b) =>
      b.product - a.product ||
      b.spread.cp - a.spread.cp ||
      a.spread.ivs.atk - b.spread.ivs.atk ||
      a.spread.ivs.def - b.spread.ivs.def ||
      a.spread.ivs.sta - b.spread.ivs.sta
  );

  const spreads = scored.map(({ spread }) => spread);
  const ranks = new Map(spreads.map((s, i) => [spreadKey(s.ivs), i + 1]));

  return { spreads, ranks };
}
