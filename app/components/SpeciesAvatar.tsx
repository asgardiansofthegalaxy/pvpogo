"use client";

import { typeGradient } from "@/app/lib/types";

/**
 * Identicon for a species, drawn from its typing.
 *
 * Deliberately not official artwork. Sprites and models are Nintendo/Game
 * Freak/Creatures copyright, so this project renders its own mark instead:
 * a ramp derived from the species' types plus its initials. See DISCLAIMER.md.
 */

type Size = "sm" | "md" | "lg";

const SIZES: Record<Size, { box: string; text: string }> = {
  sm: { box: "h-9 w-9", text: "text-[0.6rem]" },
  md: { box: "h-12 w-12", text: "text-xs" },
  lg: { box: "h-14 w-14", text: "text-sm" },
};

/** "Nidoran♀" -> "NI", "Mr. Mime" -> "MM", "Farfetch'd" -> "FA" */
export function initialsFor(name: string): string {
  const words = name.split(/[\s.'’\-_]+/).filter(Boolean);
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
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

  // A dual-type species blends the two ramps; a mono-type gets a single one.
  const primary = typeGradient(types[0] ?? "normal");
  const secondary = types[1] ? typeGradient(types[1]) : null;
  const ramp = secondary
    ? `${primary.split(" ")[0]} ${secondary.split(" ")[1]}`
    : primary;

  return (
    <span
      role="img"
      aria-label={`${name}, ${types.join(" and ")} type`}
      className={`${box} ${className} inline-flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${ramp} shadow-[0_1px_3px_rgba(0,0,0,0.4)] ring-1 ring-inset ring-white/20`}
    >
      <span
        className={`${text} font-bold tracking-tight text-white [text-shadow:0_1px_2px_rgba(0,0,0,0.45)]`}
      >
        {initialsFor(name)}
      </span>
    </span>
  );
}
