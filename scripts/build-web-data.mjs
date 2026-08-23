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

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
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

const rawSpecies = readJson("pokemon.json");
const rawMoves = readJson("moves.json");
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

// Species with no stats or no moveset cannot be built into a battler; the
// engine refuses them, so the UI should not offer them either.
const species = [];
const skipped = [];

for (const [speciesId, entry] of Object.entries(rawSpecies)) {
  const stats = entry.base_stats;
  const usable =
    stats.attack > 0 &&
    stats.defense > 0 &&
    stats.stamina > 0 &&
    entry.fast_moves.length > 0 &&
    entry.charged_moves.length > 0;

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
    fastMoves: entry.fast_moves.filter((id) => moves[id]?.fast),
    chargedMoves: entry.charged_moves.filter((id) => moves[id] && !moves[id].fast),
  });
}

species.sort((a, b) => a.dex - b.dex || a.id.localeCompare(b.id));

mkdirSync(OUT_DIR, { recursive: true });
writeFileSync(join(OUT_DIR, "species.json"), JSON.stringify(species));
writeFileSync(join(OUT_DIR, "moves.json"), JSON.stringify(moves));
writeFileSync(join(OUT_DIR, "cp-multipliers.json"), JSON.stringify(cpMultipliers));

const kb = (name) =>
  Math.round(readFileSync(join(OUT_DIR, name), "utf8").length / 1024);

console.log(
  `species.json  ${species.length} entries (${kb("species.json")} KB)\n` +
    `moves.json    ${Object.keys(moves).length} entries (${kb("moves.json")} KB)\n` +
    `cp-multipliers.json  ${cpMultipliers.length} levels\n` +
    `skipped ${skipped.length} unusable species: ${skipped.join(", ")}`
);
