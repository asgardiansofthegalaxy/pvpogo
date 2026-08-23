/**
 * Type colour tokens, shared by chips and species avatars.
 *
 * Type names are factual references to the game's mechanics; the colours here
 * are this project's own choices, not lifted palettes.
 */

export const TYPE_COLORS: Record<string, string> = {
  Normal: "bg-gray-400",
  Fire: "bg-orange-500",
  Water: "bg-blue-500",
  Electric: "bg-yellow-500",
  Grass: "bg-green-500",
  Ice: "bg-cyan-300",
  Fighting: "bg-red-700",
  Poison: "bg-purple-500",
  Ground: "bg-amber-600",
  Flying: "bg-indigo-400",
  Psychic: "bg-pink-500",
  Bug: "bg-lime-500",
  Rock: "bg-stone-500",
  Ghost: "bg-purple-800",
  Dragon: "bg-indigo-700",
  Dark: "bg-gray-800",
  Steel: "bg-slate-400",
  Fairy: "bg-pink-300",
};

/** Gradient ramps used by SpeciesAvatar, one per type. */
export const TYPE_GRADIENTS: Record<string, string> = {
  Normal: "from-gray-300 to-gray-500",
  Fire: "from-orange-400 to-red-600",
  Water: "from-sky-400 to-blue-600",
  Electric: "from-yellow-300 to-amber-500",
  Grass: "from-lime-400 to-green-600",
  Ice: "from-cyan-200 to-sky-400",
  Fighting: "from-red-500 to-rose-800",
  Poison: "from-fuchsia-400 to-purple-700",
  Ground: "from-amber-400 to-yellow-700",
  Flying: "from-indigo-300 to-sky-500",
  Psychic: "from-pink-400 to-rose-600",
  Bug: "from-lime-300 to-lime-600",
  Rock: "from-stone-400 to-stone-600",
  Ghost: "from-purple-500 to-indigo-900",
  Dragon: "from-indigo-500 to-violet-800",
  Dark: "from-gray-600 to-gray-900",
  Steel: "from-slate-300 to-slate-600",
  Fairy: "from-pink-300 to-fuchsia-500",
};
