"use client";

import { Select, SelectItem, Slider } from "@heroui/react";

import MatchupPanel from "@/app/components/MatchupPanel";
import SpeciesAvatar from "@/app/components/SpeciesAvatar";
import { BoltIcon, CloseIcon, ShieldIcon } from "@/app/components/Icon";
import type { SpeciesMatchups } from "@/app/lib/matchups";
import { typeChipClass } from "@/app/lib/types";
import {
  MAX_IV,
  MAX_LEVEL,
  calculateCp,
  effectiveStats,
  statProduct,
  titleCase,
  type Move,
  type MoveTable,
  type Species,
  type Stats,
} from "@/app/lib/pokemon";

export interface TeamMember {
  species: Species;
  fastMoveId: string;
  chargedMoveIds: string[];
  level: number;
  ivs: Stats;
}

interface Props {
  member: TeamMember | null;
  index: number;
  moves: MoveTable;
  cpMultipliers: number[];
  cap: number;
  speciesById: Map<string, Species>;
  /** Precomputed ratings for this pick, or null while the league file loads. */
  matchups: SpeciesMatchups | null;
  onChange: (member: TeamMember) => void;
  onRemove: () => void;
}

export default function TeamSlot({
  member,
  index,
  moves,
  cpMultipliers,
  cap,
  speciesById,
  matchups,
  onChange,
  onRemove,
}: Props) {
  if (!member) {
    return (
      <li className="flex min-h-[5.5rem] items-center gap-3 rounded-2xl border border-dashed border-teal-400/25 px-4 py-5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-400/10 text-sm font-semibold tabular-nums text-teal-400/70">
          {index + 1}
        </span>
        <span className="text-sm text-teal-300/70">
          Pick a Pokémon to fill this slot
        </span>
      </li>
    );
  }

  const { species, ivs, level } = member;
  const cp = calculateCp(species.stats, ivs, level, cpMultipliers);
  const effective = effectiveStats(species.stats, ivs, level, cpMultipliers);
  const overCap = cp > cap;

  const fastOptions = species.fastMoves.map((id) => moves[id]).filter(Boolean);
  const chargedOptions = species.chargedMoves.map((id) => moves[id]).filter(Boolean);

  function setIv(key: keyof Stats, value: number) {
    onChange({ ...member!, ivs: { ...ivs, [key]: value } });
  }

  return (
    <li className="rounded-2xl bg-teal-950/40 p-4 ring-1 ring-teal-400/15">
      <div className="flex items-start gap-3">
        <SpeciesAvatar name={species.name} types={species.types} size="md" />

        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2">
            <h3 className="truncate text-sm font-semibold text-teal-50">
              {species.name}
            </h3>
            <span className="text-[0.65rem] tabular-nums text-teal-400/60">
              #{species.dex}
            </span>
          </div>
          <div className="mt-1 flex flex-wrap gap-1">
            {species.types.map((t) => (
              <span
                key={t}
                className={`${typeChipClass(t)} rounded px-1.5 py-px text-[0.6rem] font-medium text-white`}
              >
                {titleCase(t)}
              </span>
            ))}
          </div>
        </div>

        <div className="shrink-0 text-right">
          <p
            className={`text-xl font-bold tabular-nums leading-none ${
              overCap ? "text-rose-300" : "text-teal-100"
            }`}
          >
            {cp}
          </p>
          <p className="mt-0.5 text-[0.6rem] uppercase tracking-wide text-teal-400/60">
            CP
          </p>
        </div>

        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${species.name} from your team`}
          className="-mr-1 -mt-1 rounded-lg p-1.5 text-teal-400/60 transition-colors hover:bg-rose-500/15 hover:text-rose-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-300"
        >
          <CloseIcon />
        </button>
      </div>

      {overCap && (
        <p className="mt-3 rounded-lg bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
          {cp} CP is over the {cap.toLocaleString()} cap. Lower the level to
          make this pick legal.
        </p>
      )}

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <MoveSelect
          label="Fast move"
          icon={<BoltIcon className="h-3.5 w-3.5" />}
          options={fastOptions}
          value={member.fastMoveId}
          onChange={(id) => onChange({ ...member, fastMoveId: id })}
          describe={(m) => `${m.power} dmg · +${m.energyGain}e · ${m.turns}t`}
        />
        <MoveSelect
          label="Charged moves"
          icon={<ShieldIcon className="h-3.5 w-3.5" />}
          options={chargedOptions}
          value={member.chargedMoveIds}
          multiple
          onChangeMultiple={(ids) =>
            onChange({ ...member, chargedMoveIds: ids.slice(0, 2) })
          }
          describe={(m) => `${m.power} dmg · ${m.energy}e`}
        />
      </div>

      <div className="mt-4 space-y-3">
        <Slider
          label="Level"
          aria-label="Level"
          size="sm"
          minValue={1}
          maxValue={MAX_LEVEL}
          step={0.5}
          value={level}
          onChange={(v) =>
            onChange({ ...member, level: Array.isArray(v) ? v[0] : v })
          }
          classNames={{
            label: "text-xs text-teal-300/80",
            value: "text-xs tabular-nums text-teal-100",
            track: "bg-teal-400/15",
            filler: "bg-teal-400",
          }}
        />

        <div className="grid grid-cols-3 gap-2">
          {(["atk", "def", "sta"] as const).map((key) => (
            <label key={key} className="block">
              <span className="mb-1 block text-[0.65rem] uppercase tracking-wide text-teal-400/70">
                {key === "sta" ? "HP IV" : `${key} IV`}
              </span>
              <input
                type="number"
                min={0}
                max={MAX_IV}
                value={ivs[key]}
                onChange={(e) => {
                  const n = Number(e.target.value);
                  if (Number.isNaN(n)) return;
                  setIv(key, Math.max(0, Math.min(MAX_IV, n)));
                }}
                className="w-full rounded-lg border border-teal-400/20 bg-teal-950/60 px-2 py-1.5 text-sm tabular-nums text-teal-50 focus:border-teal-300 focus:outline-none focus:ring-1 focus:ring-teal-300"
              />
            </label>
          ))}
        </div>

        <dl className="flex justify-between rounded-lg bg-teal-400/5 px-3 py-2 text-xs">
          <Stat label="Attack" value={effective.atk.toFixed(1)} />
          <Stat label="Defense" value={effective.def.toFixed(1)} />
          <Stat label="HP" value={String(effective.sta)} />
          <Stat label="Stat product" value={statProduct(effective).toLocaleString()} />
        </dl>
      </div>

      {matchups && (
        <MatchupPanel
          matchups={matchups}
          speciesById={speciesById}
          moves={moves}
          fastMoveId={member.fastMoveId}
          chargedMoveIds={member.chargedMoveIds}
        />
      )}
    </li>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <dt className="text-[0.6rem] uppercase tracking-wide text-teal-400/60">
        {label}
      </dt>
      <dd className="mt-0.5 font-semibold tabular-nums text-teal-100">{value}</dd>
    </div>
  );
}

interface MoveSelectProps {
  label: string;
  icon: React.ReactNode;
  options: Move[];
  describe: (move: Move) => string;
  value?: string | string[];
  multiple?: boolean;
  onChange?: (id: string) => void;
  onChangeMultiple?: (ids: string[]) => void;
}

function MoveSelect({
  label,
  icon,
  options,
  describe,
  value,
  multiple,
  onChange,
  onChangeMultiple,
}: MoveSelectProps) {
  const selected = multiple
    ? new Set(value as string[])
    : new Set(value ? [value as string] : []);

  return (
    <Select
      label={
        <span className="flex items-center gap-1.5 text-teal-300/80">
          {icon}
          {label}
        </span>
      }
      aria-label={label}
      size="sm"
      selectionMode={multiple ? "multiple" : "single"}
      selectedKeys={selected}
      disallowEmptySelection={!multiple}
      onSelectionChange={(keys) => {
        const ids = Array.from(keys as Set<string>);
        if (multiple) onChangeMultiple?.(ids);
        else if (ids[0]) onChange?.(ids[0]);
      }}
      classNames={{
        trigger:
          "bg-teal-950/60 border border-teal-400/20 data-[hover=true]:border-teal-400/40",
        value: "text-teal-50 text-xs",
        popoverContent: "bg-teal-950 border border-teal-400/20",
      }}
    >
      {options.map((move) => (
        <SelectItem key={move.id} textValue={move.name}>
          <span className="flex items-baseline justify-between gap-3">
            <span className="text-teal-50">{move.name}</span>
            <span className="text-[0.65rem] tabular-nums text-teal-400/70">
              {describe(move)}
            </span>
          </span>
        </SelectItem>
      ))}
    </Select>
  );
}
