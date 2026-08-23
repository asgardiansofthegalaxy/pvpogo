"use client";

import { TYPE_GRADIENTS } from "@/app/lib/types";

/**
 * Identicon for a species, drawn from its typing.
 *
 * Deliberately not official artwork. Sprites and models are Nintendo/Game
 * Freak/Creatures copyright, so this project renders its own mark instead:
 * a gradient derived from the species' types plus its initials. See
 * DISCLAIMER.md.
 */

type Size = "sm" | "md" | "lg";

const SIZES: Record<Size, { box: string; text: string }> = {
  sm: { box: "w-10 h-10", text: "text-[0.65rem]" },
  md: { box: "w-12 h-12", text: "text-xs" },
  lg: { box: "w-16 h-16", text: "text-sm" },
};

/** "Nidoran♀" -> "NI", "Mr. Mime" -> "MM", "Farfetch'd" -> "FA" */
export function initialsFor(name: string): string {
  const words = name.split(/[\s.'-]+/).filter(Boolean);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return (words[0] ?? name).slice(0, 2).toUpperCase();
}

export interface SpeciesAvatarProps {
  name: string;
  types: readonly string[];
  size?: Size;
  className?: string;
}

export default function SpeciesAvatar({
  name,
  types,
  size = "md",
  className = "",
}: SpeciesAvatarProps) {
  const { box, text } = SIZES[size];
  const gradient = TYPE_GRADIENTS[types[0]] ?? "from-gray-400 to-gray-600";
  // A dual-type species blends both colours; a mono-type gets a single ramp.
  const secondary = types[1] ? TYPE_GRADIENTS[types[1]] : undefined;
  const blend = secondary ? `${gradient.split(" ")[0]} ${secondary.split(" ")[1]}` : gradient;

  return (
    <div
      role="img"
      aria-label={`${name}, ${types.join(" and ")} type`}
      title={name}
      className={`${box} ${className} shrink-0 rounded-full bg-gradient-to-br ${blend} flex items-center justify-center ring-1 ring-white/25 shadow-sm select-none`}
    >
      <span className={`${text} font-bold tracking-tight text-white drop-shadow`}>
        {initialsFor(name)}
      </span>
    </div>
  );
}
