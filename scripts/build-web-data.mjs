#!/usr/bin/env node
/**
 * Export the engine's dataset into something the browser can use.
 *
 * The Python engine owns the data (pypogo/pypogo/game_master/*.json). This
 * trims it to the fields the UI needs and writes public/data/*.json, so the
 * frontend depends on the dataset without depending on a running Python
 * service. Runs as `prebuild`; also run it by hand after regenerating the
 * dataset.
 *
 * Reads JSON only, so it needs no Python toolchain.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const ENGINE_DATA = join(ROOT, "pypogo", "pypogo", "game_master");
const OUT_DIR = join(ROOT, "public", "data");

/** Level -> CP multiplier, indexed as CP_MULTIPLIER[(level - 1) * 2]. */
const CP_MULTIPLIER_SOURCE = join(ROOT, "pypogo", "pypogo", "constants.py");

function readJson(name) {
  return JSON.parse(readFileSync(join(ENGINE_DATA, name), "utf8"));
}

/**
 * Pull the CP multiplier table out of constants.py rather than duplicating 109
 * magic floats by hand, so the two can never drift.
 */
function readCpMultipliers() {
  const source = readFileSync(CP_MULTIPLIER_SOURCE, "utf8");
  const block = source.split("CP_MULTIPLIER = [")[1]?.split("]")[0];
  if (!block) throw new Error("Could not find CP_MULTIPLIER in constants.py");

  const values = block
    .split("\n")
    .map((line) => line.replace(/#.*$/, "").trim().replace(/,$/, ""))
    .filter((line) => line.length > 0)
    .map(Number);

  if (values.some(Number.isNaN)) throw new Error("CP_MULTIPLIER has a non-numeric entry");
  return values;
}

/** Leagues that ship a precomputed matchup file. Mirrors LEAGUE_KEYS in meta.py. */
const LEAGUES = ["great", "ultra", "master"];

/**
 * Matchups per species kept in a league's summary file.
 *
 * The engine file holds a full row -- every species against all ~100 meta
 * picks. A pick's panel only ever shows its best and worst few, so the summary
 * carries those plus a mean and stays small enough to load with the page.
 * The full matrix ships beside it in `matchups.<league>.rows.json`, which the
 * team builder fetches only once there is a team to analyse: 182 KB gzipped
 * against the summary's 82 KB, and nobody browsing the roster pays for it.
 */
const KEPT_MATCHUPS = 6;

function readMatchupFile(league) {
  const path = join(ENGINE_DATA, `matchups.${league}.json`);
  if (!existsSync(path)) {
    throw new Error(
      `Missing ${path}. Regenerate it with:\n` +
        `  cd pypogo && python3 pypogo/scripts/build_matchups.py --league ${league}`
    );
  }
  return JSON.parse(readFileSync(path, "utf8"));
}

/**
 * Every species' full row, for team-level coverage analysis.
 *
 * `meta` repeats the column order the ratings are indexed by. The two files
 * are written together from one engine file so they cannot disagree, and
 * carrying the ids means the browser can tell if they ever do rather than
 * lining up a row against the wrong opponent.
 */
function matchupRows(raw) {
  return {
    league: raw.league,
    meta: raw.meta.map(({ id }) => id),
    ratings: raw.ratings,
  };
}

function trimMatchups(raw) {
  const best = {};
  const worst = {};
  const score = {};

  for (const [speciesId, ratings] of Object.entries(raw.ratings)) {
    // A species' own column rates ~500 by construction and says nothing, so
    // it is dropped rather than shown as a middling matchup against itself.
    const ranked = ratings
      .map((rating, index) => [index, rating])
      .filter(([index]) => raw.meta[index].id !== speciesId)
      .sort((a, b) => b[1] - a[1]);

    if (ranked.length === 0) continue;

    best[speciesId] = ranked.slice(0, KEPT_MATCHUPS);
    worst[speciesId] = ranked.slice(-KEPT_MATCHUPS).reverse();
    score[speciesId] = Math.round(
      ranked.reduce((sum, [, rating]) => sum + rating, 0) / ranked.length
    );
  }

  return {
    league: raw.league,
    cap: raw.cap,
    assumptions: raw.assumptions,
    meta: raw.meta.map(({ id, cp, level, fast, charged }) => ({
      id,
      cp,
      level,
      fast,
      charged,
    })),
    builds: raw.builds,
    best,
    worst,
    score,
    aliases: raw.aliases,
  };
}

const rawSpecies = readJson("pokemon.json");
const rawMoves = readJson("moves.json");
const rankings = readJson("movesets.json").rankings;
const cpMultipliers = readCpMultipliers();

// Keyed by move_id, which is how species reference their move pools.
const moves = {};
for (const entry of Object.values(rawMoves)) {
  moves[entry.move_id] = {
    id: entry.move_id,
    name: entry.name.replace(/ Fast$/, ""),
    type: entry.move_type,
    fast: entry.is_fast,
    power: entry.power,
    energy: entry.energy,
    energyGain: entry.energy_gain,
    // Stored in ms upstream; the engine's turn is 500ms.
    turns: entry.cooldown / 500,
    buff: entry.buff ?? null,
  };
}

/**
 * A species' move pool, ranked best first.
 *
 * The dataset lists moves in the order the export happened to carry them,
 * which is not a ranking -- Azumarill leads with Rock Smash. pypogo/movesets.py
 * ranks them, and the matchup matrices are built on its answer, so ordering
 * the pools by it here is what makes the UI's `fastMoves[0]` the same moveset
 * the matrix describes.
 *
 * Throws if the ranking and the dataset disagree about what a species can run,
 * which is what a stale movesets.json looks like.
 */
function rankedPool(speciesId, declared, ranked, isUsable) {
  const usable = declared.filter(isUsable);
  const ordered = ranked.filter(isUsable);

  if (ordered.length !== usable.length || !ordered.every((id) => usable.includes(id))) {
    throw new Error(
      `movesets.json disagrees with pokemon.json about ${speciesId}: ranked ` +
        `[${ordered}] against declared [${usable}]. Regenerate it with:\n` +
        `  cd pypogo && python3 pypogo/scripts/build_movesets.py`
    );
  }
  return ordered;
}

// Species with no stats or no battle-usable moveset cannot be built into a
// battler; the engine refuses them, so the UI should not offer them either.
// The ranking is absent for exactly those the engine refuses -- nine species
// declare Struggle as their entire pool -- so its coverage is the test.
const species = [];
const skipped = [];

for (const [speciesId, entry] of Object.entries(rawSpecies)) {
  const stats = entry.base_stats;
  const ranked = rankings[speciesId];
  const usable =
    stats.attack > 0 && stats.defense > 0 && stats.stamina > 0 && ranked !== undefined;

  if (!usable) {
    skipped.push(speciesId);
    continue;
  }

  species.push({
    id: speciesId,
    name: entry.species_name,
    dex: entry.dex_number,
    // Upstream pads the second slot with "none" for mono-type species.
    types: entry.types.filter((t) => t && t !== "none"),
    stats: {
      atk: stats.attack,
      def: stats.defense,
      sta: stats.stamina,
    },
    fastMoves: rankedPool(
      speciesId,
      entry.fast_moves,
      ranked.fast,
      (id) => moves[id]?.fast === true
    ),
    chargedMoves: rankedPool(
      speciesId,
      entry.charged_moves,
      ranked.charged,
      (id) => moves[id] !== undefined && !moves[id].fast
    ),
  });
}

species.sort((a, b) => a.dex - b.dex || a.id.localeCompare(b.id));

mkdirSync(OUT_DIR, { recursive: true });
writeFileSync(join(OUT_DIR, "species.json"), JSON.stringify(species));
writeFileSync(join(OUT_DIR, "moves.json"), JSON.stringify(moves));
writeFileSync(join(OUT_DIR, "cp-multipliers.json"), JSON.stringify(cpMultipliers));

const kb = (name) =>
  Math.round(readFileSync(join(OUT_DIR, name), "utf8").length / 1024);

const matchupSummary = LEAGUES.map((league) => {
  const raw = readMatchupFile(league);

  const trimmed = trimMatchups(raw);
  const name = `matchups.${league}.json`;
  writeFileSync(join(OUT_DIR, name), JSON.stringify(trimmed));

  const rows = matchupRows(raw);
  const rowsName = `matchups.${league}.rows.json`;
  writeFileSync(join(OUT_DIR, rowsName), JSON.stringify(rows));

  return (
    `${name}  ${trimmed.meta.length} meta, ${Object.keys(trimmed.best).length} species (${kb(name)} KB)\n` +
    `${rowsName}  ${Object.keys(rows.ratings).length} full rows (${kb(rowsName)} KB)`
  );
}).join("\n");

console.log(
  `species.json  ${species.length} entries, moves ranked (${kb("species.json")} KB)\n` +
    `moves.json    ${Object.keys(moves).length} entries (${kb("moves.json")} KB)\n` +
    `cp-multipliers.json  ${cpMultipliers.length} levels\n` +
    `${matchupSummary}\n` +
    `skipped ${skipped.length} unusable species: ${skipped.join(", ")}`
);
