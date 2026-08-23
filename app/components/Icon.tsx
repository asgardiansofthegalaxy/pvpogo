/**
 * The project's icon set: authored SVG on a single 24px grid at a consistent
 * 1.75 stroke, so nothing here is an emoji or a unicode glyph standing in for
 * a drawn mark.
 */

interface IconProps {
  className?: string;
  "aria-hidden"?: boolean;
}

const BASE = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function SearchIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg {...BASE} className={className} aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

export function CloseIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg {...BASE} className={className} aria-hidden="true">
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}

export function PlusIcon({ className = "h-5 w-5" }: IconProps) {
  return (
    <svg {...BASE} className={className} aria-hidden="true">
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function BoltIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg {...BASE} className={className} aria-hidden="true">
      <path d="M13 3 5 14h6l-1 7 8-11h-6l1-7Z" />
    </svg>
  );
}

export function ShieldIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg {...BASE} className={className} aria-hidden="true">
      <path d="M12 3.5 5 6.2v5c0 4.2 2.9 7.6 7 9.3 4.1-1.7 7-5.1 7-9.3v-5L12 3.5Z" />
    </svg>
  );
}
