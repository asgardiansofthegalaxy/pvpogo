"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import SpeciesPicker from "@/app/components/SpeciesPicker";
import TeamCoveragePanel from "@/app/components/TeamCoverage";
import TeamSlot, { type TeamMember } from "@/app/components/TeamSlot";
import {
  buildFor,
  loadMatchupRows,
  loadMatchups,
  matchupsFor,
  teamCoverage,
  type MatchupData,
  type MatchupRows,
} from "@/app/lib/matchups";
import {
  LEAGUES,
  TEAM_SIZE,
  loadData,
  maxLevelUnderCap,
  type LeagueKey,
  type LoadedData,
  type Species,
} from "@/app/lib/pokemon";

/** Great League spreads favour bulk, so default to a rank-1-ish spread. */
const DEFAULT_IVS = { atk: 0, def: 15, sta: 15 };

export default function TeamBuilder() {
  const [data, setData] = useState<LoadedData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [league, setLeague] = useState<LeagueKey>("great");
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [matchups, setMatchups] = useState<MatchupData | null>(null);
  const [rows, setRows] = useState<MatchupRows | null>(null);

  useEffect(() => {
    let live = true;
    loadData()
      .then((d) => {
        if (live) setData(d);
      })
      .catch(() => {
        if (live) setError("Could not load Pokémon data.");
      });
    return () => {
      live = false;
    };
  }, []);

  // Matchup ratings are league-specific, so clear them while the new league's
  // file loads rather than showing Great League numbers under an Ultra tab.
  useEffect(() => {
    let live = true;
    setMatchups(null);
    loadMatchups(league)
      .then((d) => {
        if (live) setMatchups(d);
      })
      .catch(() => {
        // Matchups are an enhancement; the builder still works without them.
      });
    return () => {
      live = false;
    };
  }, [league]);

  // The full matrix is the larger half of the data and only the coverage panel
  // reads it, so it is fetched once there is a team to analyse rather than on
  // page load. Browsing the roster never pays for it.
  const hasTeam = team.length > 0;

  useEffect(() => {
    setRows(null);
    if (!hasTeam) return;

    let live = true;
    loadMatchupRows(league)
      .then((d) => {
        if (live) setRows(d);
      })
      .catch(() => {
        // Coverage is an enhancement; the per-pick panels still work without it.
      });
    return () => {
      live = false;
    };
  }, [league, hasTeam]);

  const cap = LEAGUES[league].cap;

  // Re-cap the team when the league changes: a Great League build is a
  // different Pokémon at Ultra, and leaving it over the cap would be showing
  // an illegal team.
  useEffect(() => {
    if (!data) return;
    setTeam((current) =>
      current.map((m) => ({
        ...m,
        level:
          maxLevelUnderCap(m.species.stats, m.ivs, cap, data.cpMultipliers) ??
          m.level,
      }))
    );
  }, [cap, data]);

  const chosenIds = useMemo(() => team.map((m) => m.species.id), [team]);
  const speciesById = useMemo(
    () => new Map((data?.species ?? []).map((s) => [s.id, s])),
    [data]
  );
  const full = team.length >= TEAM_SIZE;

  const coverage = useMemo(
    () =>
      matchups && rows && chosenIds.length > 0
        ? teamCoverage(matchups, rows, chosenIds)
        : null,
    [matchups, rows, chosenIds]
  );

  /**
   * The moveset a fresh pick starts with.
   *
   * The exported pools are ordered by pypogo/movesets.py, so their first
   * entries are already the ranked choice rather than whatever order the
   * dataset carried -- no more Rock Smash Azumarill. When the league's matchup
   * file has loaded, the build it was simulated with is better still, since a
   * meta pick's moveset was brute-forced rather than scored, and starting
   * there means the panel's ratings describe the Pokémon actually in the slot.
   */
  function defaultMoveset(species: Species) {
    const build = matchups ? buildFor(matchups, species.id) : null;
    return build
      ? { fastMoveId: build.fast, chargedMoveIds: build.charged.slice(0, 2) }
      : {
          fastMoveId: species.fastMoves[0],
          chargedMoveIds: species.chargedMoves.slice(0, 2),
        };
  }

  function addSpecies(species: Species) {
    if (!data || full || chosenIds.includes(species.id)) return;

    const level =
      maxLevelUnderCap(species.stats, DEFAULT_IVS, cap, data.cpMultipliers) ?? 1;

    setTeam((current) => [
      ...current,
      {
        species,
        ...defaultMoveset(species),
        level,
        ivs: DEFAULT_IVS,
      },
    ]);
  }

  const slots = Array.from({ length: TEAM_SIZE }, (_, i) => team[i] ?? null);

  return (
    <main className="min-h-screen bg-gradient-to-b from-teal-900 via-teal-950 to-teal-950">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-12">
        <header className="mb-8">
          <Link
            href="/"
            className="rounded text-xs font-medium text-teal-300/70 transition-colors hover:text-teal-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300"
          >
            ← PvPogo
          </Link>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-teal-50 sm:text-4xl">
            Team Builder
          </h1>
          <p className="mt-2 max-w-prose text-sm text-teal-300/80">
            Build a Battle League team of three. Every pick starts at the
            highest level its CP cap allows.
          </p>

          <div
            role="tablist"
            aria-label="League"
            className="mt-6 inline-flex rounded-xl bg-teal-950/60 p-1 ring-1 ring-teal-400/15"
          >
            {(Object.keys(LEAGUES) as LeagueKey[]).map((key) => {
              const active = key === league;
              return (
                <button
                  key={key}
                  role="tab"
                  aria-selected={active}
                  onClick={() => setLeague(key)}
                  className={`whitespace-nowrap rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300 sm:text-sm ${
                    active
                      ? "bg-teal-400 text-teal-950"
                      : "text-teal-200/80 hover:text-teal-100"
                  }`}
                >
                  <span className="hidden sm:inline">{LEAGUES[key].name}</span>
                  <span className="sm:hidden">{LEAGUES[key].short}</span>
                  <span className="ml-1.5 tabular-nums opacity-70">
                    {key === "master" ? "∞" : LEAGUES[key].cap}
                  </span>
                </button>
              );
            })}
          </div>
        </header>

        {error ? (
          <p className="rounded-2xl bg-rose-500/10 px-4 py-6 text-sm text-rose-200">
            {error} Try reloading the page.
          </p>
        ) : !data ? (
          <LoadingState />
        ) : (
          <div className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,1fr)_26rem]">
            <SpeciesPicker
              species={data.species}
              cpMultipliers={data.cpMultipliers}
              cap={cap}
              chosenIds={chosenIds}
              disabled={full}
              onPick={addSpecies}
            />

            <section
              aria-label="Your team"
              className="min-w-0 lg:sticky lg:top-6 lg:self-start"
            >
              <div className="mb-3 flex items-baseline justify-between">
                <h2 className="text-base font-semibold text-teal-50">Your team</h2>
                <p className="text-xs tabular-nums text-teal-300/80">
                  {team.length}/{TEAM_SIZE} selected
                </p>
              </div>

              <ul className="space-y-3">
                {slots.map((member, i) => (
                  <TeamSlot
                    key={member?.species.id ?? `empty-${i}`}
                    member={member}
                    index={i}
                    moves={data.moves}
                    cpMultipliers={data.cpMultipliers}
                    cap={cap}
                    leagueName={LEAGUES[league].short}
                    speciesById={speciesById}
                    matchups={
                      matchups && member
                        ? matchupsFor(matchups, member.species.id)
                        : null
                    }
                    onChange={(next) =>
                      setTeam((current) =>
                        current.map((m) =>
                          m.species.id === next.species.id ? next : m
                        )
                      )
                    }
                    onRemove={() =>
                      setTeam((current) =>
                        current.filter((m) => m.species.id !== member?.species.id)
                      )
                    }
                  />
                ))}
              </ul>

              <div className="mt-3">
                <TeamCoveragePanel
                  coverage={coverage}
                  speciesById={speciesById}
                  picked={team.length}
                  teamSize={TEAM_SIZE}
                />
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}

function LoadingState() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,1fr)_26rem]"
    >
      <span className="sr-only">Loading Pokémon data</span>
      <div className="h-96 animate-pulse rounded-2xl bg-teal-950/40 ring-1 ring-teal-400/10" />
      <div className="space-y-3">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-24 animate-pulse rounded-2xl bg-teal-950/40 ring-1 ring-teal-400/10"
          />
        ))}
      </div>
    </div>
  );
}
