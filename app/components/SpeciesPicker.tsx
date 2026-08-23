"use client";

import { useMemo, useState } from "react";
import { Input, ScrollShadow } from "@heroui/react";

import SpeciesAvatar from "@/app/components/SpeciesAvatar";
import { SearchIcon } from "@/app/components/Icon";
import { typeChipClass } from "@/app/lib/types";
import {
  ALL_TYPES,
  calculateCp,
  maxLevelUnderCap,
  titleCase,
  type Species,
} from "@/app/lib/pokemon";

/** Rendering 1279 rows at once janks the list; results beyond this are paged in. */
const PAGE = 60;

const PERFECT_IVS = { atk: 15, def: 15, sta: 15 };

interface Props {
  species: Species[];
  cpMultipliers: number[];
  cap: number;
  chosenIds: string[];
  disabled: boolean;
  onPick: (species: Species) => void;
}

export default function SpeciesPicker({
  species,
  cpMultipliers,
  cap,
  chosenIds,
  disabled,
  onPick,
}: Props) {
  const [query, setQuery] = useState("");
  const [activeType, setActiveType] = useState<string | null>(null);
  const [shown, setShown] = useState(PAGE);

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return species.filter((s) => {
      if (activeType && !s.types.includes(activeType)) return false;
      if (!needle) return true;
      return s.name.toLowerCase().includes(needle) || String(s.dex) === needle;
    });
  }, [species, query, activeType]);

  const visible = results.slice(0, shown);

  function reset(next: () => void) {
    next();
    setShown(PAGE);
  }

  return (
    <section
      aria-label="Choose Pokémon"
      className="flex min-h-0 min-w-0 flex-col rounded-2xl bg-teal-950/40 ring-1 ring-teal-400/15"
    >
      <div className="space-y-3 border-b border-teal-400/10 p-4 sm:p-5">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="text-base font-semibold text-teal-50">Choose Pokémon</h2>
          <p className="text-xs tabular-nums text-teal-300/80">
            {results.length.toLocaleString()} of {species.length.toLocaleString()}
          </p>
        </div>

        <Input
          aria-label="Search Pokémon by name or Pokédex number"
          placeholder="Search Pokémon..."
          value={query}
          onValueChange={(v) => reset(() => setQuery(v))}
          variant="bordered"
          startContent={<SearchIcon className="h-4 w-4 text-teal-400/70" />}
          classNames={{
            input: "text-teal-50 placeholder:text-teal-400/50",
            inputWrapper:
              "border-teal-400/25 data-[hover=true]:border-teal-400/50 group-data-[focus=true]:border-teal-300 bg-teal-950/50",
          }}
        />

        <div className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1 [scrollbar-width:none] sm:flex-wrap sm:overflow-visible [&::-webkit-scrollbar]:hidden">
          <FilterChip
            label="All"
            active={activeType === null}
            onClick={() => reset(() => setActiveType(null))}
          />
          {ALL_TYPES.map((type) => (
            <FilterChip
              key={type}
              label={titleCase(type)}
              active={activeType === type}
              colorClass={typeChipClass(type)}
              onClick={() =>
                reset(() => setActiveType(activeType === type ? null : type))
              }
            />
          ))}
        </div>
      </div>

      <ScrollShadow className="max-h-[26rem] flex-1 p-3 sm:max-h-[32rem]">
        {results.length === 0 ? (
          <p className="px-2 py-10 text-center text-sm text-teal-300/70">
            No Pokémon match {query ? `“${query}”` : "that filter"}.
          </p>
        ) : (
          <ul className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {visible.map((s) => {
              const level = maxLevelUnderCap(s.stats, PERFECT_IVS, cap, cpMultipliers);
              const cp = level
                ? calculateCp(s.stats, PERFECT_IVS, level, cpMultipliers)
                : null;
              const chosen = chosenIds.includes(s.id);

              return (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => onPick(s)}
                    disabled={disabled || chosen}
                    aria-label={`Add ${s.name} to your team`}
                    className="group flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left transition-colors duration-150 hover:bg-teal-400/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
                  >
                    <SpeciesAvatar name={s.name} types={s.types} size="sm" />
                    <span className="min-w-0 flex-1">
                      <span className="flex items-baseline gap-2">
                        <span className="truncate text-sm font-medium text-teal-50">
                          {s.name}
                        </span>
                        <span className="shrink-0 text-[0.65rem] tabular-nums text-teal-400/60">
                          #{s.dex}
                        </span>
                      </span>
                      <span className="mt-1 flex gap-1">
                        {s.types.map((t) => (
                          <span
                            key={t}
                            className={`${typeChipClass(t)} rounded px-1.5 py-px text-[0.6rem] font-medium text-white`}
                          >
                            {titleCase(t)}
                          </span>
                        ))}
                      </span>
                    </span>
                    <span className="shrink-0 text-right">
                      {chosen ? (
                        <span className="block text-[0.65rem] font-medium text-teal-300">
                          On team
                        </span>
                      ) : (
                        <>
                          <span className="block text-sm font-semibold tabular-nums text-teal-100">
                            {cp ?? "—"}
                          </span>
                          <span className="block text-[0.6rem] text-teal-400/60">
                            CP
                          </span>
                        </>
                      )}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}

        {shown < results.length && (
          <button
            type="button"
            onClick={() => setShown((n) => n + PAGE)}
            className="mt-3 w-full rounded-xl border border-teal-400/20 py-2.5 text-sm font-medium text-teal-200 transition-colors hover:bg-teal-400/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300"
          >
            Show {Math.min(PAGE, results.length - shown)} more
          </button>
        )}
      </ScrollShadow>
    </section>
  );
}

function FilterChip({
  label,
  active,
  colorClass,
  onClick,
}: {
  label: string;
  active: boolean;
  colorClass?: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`shrink-0 whitespace-nowrap rounded-full px-2.5 py-1 text-[0.7rem] font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300 ${
        active
          ? `${colorClass ?? "bg-teal-400"} text-white ring-1 ring-white/30`
          : "bg-teal-400/10 text-teal-200/80 hover:bg-teal-400/20"
      }`}
    >
      {label}
    </button>
  );
}
