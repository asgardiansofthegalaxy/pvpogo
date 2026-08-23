/**
 * Type colour tokens, shared by chips and species marks.
 *
 * Type names are factual references to the game's mechanics; the colours here
 * are this project's own choices, not lifted palettes. The dataset stores types
 * lowercase, so every lookup normalises first.
 */

const CHIP: Record<string, string> = {
  normal: "bg-stone-400/90",
  fire: "bg-orange-500/90",
  water: "bg-sky-500/90",
  electric: "bg-amber-400/90",
  grass: "bg-green-500/90",
  ice: "bg-cyan-400/90",
  fighting: "bg-rose-600/90",
  poison: "bg-fuchsia-600/90",
  ground: "bg-amber-600/90",
  flying: "bg-indigo-400/90",
  psychic: "bg-pink-500/90",
  bug: "bg-lime-500/90",
  rock: "bg-stone-500/90",
  ghost: "bg-violet-700/90",
  dragon: "bg-indigo-600/90",
  dark: "bg-neutral-700/90",
  steel: "bg-slate-400/90",
  fairy: "bg-pink-400/90",
};

const GRADIENT: Record<string, string> = {
  normal: "from-stone-300 to-stone-500",
  fire: "from-orange-400 to-red-600",
  water: "from-sky-400 to-blue-600",
  electric: "from-amber-300 to-yellow-500",
  grass: "from-lime-400 to-green-600",
  ice: "from-cyan-200 to-sky-500",
  fighting: "from-rose-500 to-rose-800",
  poison: "from-fuchsia-400 to-purple-700",
  ground: "from-amber-400 to-yellow-700",
  flying: "from-indigo-300 to-sky-500",
  psychic: "from-pink-400 to-rose-600",
  bug: "from-lime-300 to-lime-600",
  rock: "from-stone-400 to-stone-600",
  ghost: "from-violet-500 to-indigo-900",
  dragon: "from-indigo-500 to-violet-800",
  dark: "from-neutral-600 to-neutral-900",
  steel: "from-slate-300 to-slate-600",
  fairy: "from-pink-300 to-fuchsia-500",
};

export function typeChipClass(type: string): string {
  return CHIP[type.toLowerCase()] ?? "bg-stone-500/90";
}

export function typeGradient(type: string): string {
  return GRADIENT[type.toLowerCase()] ?? "from-stone-400 to-stone-600";
}
