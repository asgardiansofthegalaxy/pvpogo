"use client";

import { useState } from "react";
import {
  Card,
  CardBody,
  CardHeader,
  Chip,
  Button,
  Badge,
  Input,
  Selection,
  ScrollShadow,
} from "@heroui/react";
import { Pokemon } from "./types";
import SpeciesAvatar from "@/app/components/SpeciesAvatar";
import { TYPE_COLORS } from "@/app/lib/types";

const POKEMON_LIST: Pokemon[] = [
  { id: "bulbasaur", name: "Bulbasaur", types: ["Grass", "Poison"], dex: 1 },
  { id: "ivysaur", name: "Ivysaur", types: ["Grass", "Poison"], dex: 2 },
  { id: "venusaur", name: "Venusaur", types: ["Grass", "Poison"], dex: 3 },
  { id: "charmander", name: "Charmander", types: ["Fire"], dex: 4 },
  { id: "charmeleon", name: "Charmeleon", types: ["Fire"], dex: 5 },
  { id: "charizard", name: "Charizard", types: ["Fire", "Flying"], dex: 6 },
  { id: "squirtle", name: "Squirtle", types: ["Water"], dex: 7 },
  { id: "wartortle", name: "Wartortle", types: ["Water"], dex: 8 },
  { id: "blastoise", name: "Blastoise", types: ["Water"], dex: 9 },
  { id: "pikachu", name: "Pikachu", types: ["Electric"], dex: 25 },
  { id: "raichu", name: "Raichu", types: ["Electric"], dex: 26 },
  { id: "sandshrew", name: "Sandshrew", types: ["Ground"], dex: 27 },
  { id: "sandslash", name: "Sandslash", types: ["Ground"], dex: 28 },
  { id: "nidoran-f", name: "Nidoran♀", types: ["Poison"], dex: 29 },
  { id: "nidorina", name: "Nidorina", types: ["Poison"], dex: 30 },
  { id: "nidoqueen", name: "Nidoqueen", types: ["Poison", "Ground"], dex: 31 },
  { id: "nidoran-m", name: "Nidoran♂", types: ["Poison"], dex: 32 },
  { id: "nidorino", name: "Nidorino", types: ["Poison"], dex: 33 },
  { id: "nidoking", name: "Nidoking", types: ["Poison", "Ground"], dex: 34 },
  { id: "clefairy", name: "Clefairy", types: ["Fairy"], dex: 35 },
  { id: "clefable", name: "Clefable", types: ["Fairy"], dex: 36 },
  { id: "vulpix", name: "Vulpix", types: ["Fire"], dex: 37 },
  { id: "ninetales", name: "Ninetales", types: ["Fire"], dex: 38 },
  { id: "jigglypuff", name: "Jigglypuff", types: ["Normal", "Fairy"], dex: 39 },
  { id: "wigglytuff", name: "Wigglytuff", types: ["Normal", "Fairy"], dex: 40 },
  { id: "zubat", name: "Zubat", types: ["Poison", "Flying"], dex: 41 },
  { id: "golbat", name: "Golbat", types: ["Poison", "Flying"], dex: 42 },
  { id: "oddish", name: "Oddish", types: ["Grass", "Poison"], dex: 43 },
  { id: "gloom", name: "Gloom", types: ["Grass", "Poison"], dex: 44 },
  { id: "vileplume", name: "Vileplume", types: ["Grass", "Poison"], dex: 45 },
  { id: "paras", name: "Paras", types: ["Bug", "Grass"], dex: 46 },
  { id: "parasect", name: "Parasect", types: ["Bug", "Grass"], dex: 47 },
  { id: "venonat", name: "Venonat", types: ["Bug", "Poison"], dex: 48 },
  { id: "venomoth", name: "Venomoth", types: ["Bug", "Poison"], dex: 49 },
  { id: "diglett", name: "Diglett", types: ["Ground"], dex: 50 },
  { id: "dugtrio", name: "Dugtrio", types: ["Ground"], dex: 51 },
  { id: "meowth", name: "Meowth", types: ["Normal"], dex: 52 },
  { id: "persian", name: "Persian", types: ["Normal"], dex: 53 },
  { id: "psyduck", name: "Psyduck", types: ["Water"], dex: 54 },
  { id: "golduck", name: "Golduck", types: ["Water"], dex: 55 },
  { id: "mankey", name: "Mankey", types: ["Fighting"], dex: 56 },
  { id: "primeape", name: "Primeape", types: ["Fighting"], dex: 57 },
  { id: "growlithe", name: "Growlithe", types: ["Fire"], dex: 58 },
  { id: "arcanine", name: "Arcanine", types: ["Fire"], dex: 59 },
  { id: "poliwag", name: "Poliwag", types: ["Water"], dex: 60 },
  { id: "poliwhirl", name: "Poliwhirl", types: ["Water"], dex: 61 },
  { id: "poliwrath", name: "Poliwrath", types: ["Water", "Fighting"], dex: 62 },
  { id: "abra", name: "Abra", types: ["Psychic"], dex: 63 },
  { id: "kadabra", name: "Kadabra", types: ["Psychic"], dex: 64 },
  { id: "alakazam", name: "Alakazam", types: ["Psychic"], dex: 65 },
  { id: "machop", name: "Machop", types: ["Fighting"], dex: 66 },
  { id: "machoke", name: "Machoke", types: ["Fighting"], dex: 67 },
  { id: "machamp", name: "Machamp", types: ["Fighting"], dex: 68 },
  { id: "bellsprout", name: "Bellsprout", types: ["Grass", "Poison"], dex: 69 },
  { id: "weepinbell", name: "Weepinbell", types: ["Grass", "Poison"], dex: 70 },
  { id: "victreebel", name: "Victreebel", types: ["Grass", "Poison"], dex: 71 },
  { id: "tentacool", name: "Tentacool", types: ["Water", "Poison"], dex: 72 },
  { id: "tentacruel", name: "Tentacruel", types: ["Water", "Poison"], dex: 73 },
  { id: "geodude", name: "Geodude", types: ["Rock", "Ground"], dex: 74 },
  { id: "graveler", name: "Graveler", types: ["Rock", "Ground"], dex: 75 },
  { id: "golem", name: "Golem", types: ["Rock", "Ground"], dex: 76 },
  { id: "ponyta", name: "Ponyta", types: ["Fire"], dex: 77 },
  { id: "rapidash", name: "Rapidash", types: ["Fire"], dex: 78 },
  { id: "slowpoke", name: "Slowpoke", types: ["Water", "Psychic"], dex: 79 },
  { id: "slowbro", name: "Slowbro", types: ["Water", "Psychic"], dex: 80 },
  { id: "magnemite", name: "Magnemite", types: ["Electric", "Steel"], dex: 81 },
  { id: "magneton", name: "Magneton", types: ["Electric", "Steel"], dex: 82 },
  { id: "farfetchd", name: "Farfetch'd", types: ["Normal", "Flying"], dex: 83 },
  { id: "doduo", name: "Doduo", types: ["Normal", "Flying"], dex: 84 },
  { id: "dodrio", name: "Dodrio", types: ["Normal", "Flying"], dex: 85 },
  { id: "seel", name: "Seel", types: ["Water"], dex: 86 },
  { id: "dewgong", name: "Dewgong", types: ["Water", "Ice"], dex: 87 },
  { id: "grimer", name: "Grimer", types: ["Poison"], dex: 88 },
  { id: "muk", name: "Muk", types: ["Poison"], dex: 89 },
  { id: "shellder", name: "Shellder", types: ["Water"], dex: 90 },
  { id: "cloyster", name: "Cloyster", types: ["Water", "Ice"], dex: 91 },
  { id: "gastly", name: "Gastly", types: ["Ghost", "Poison"], dex: 92 },
  { id: "haunter", name: "Haunter", types: ["Ghost", "Poison"], dex: 93 },
  { id: "gengar", name: "Gengar", types: ["Ghost", "Poison"], dex: 94 },
  { id: "onix", name: "Onix", types: ["Rock", "Ground"], dex: 95 },
  { id: "hypno", name: "Hypno", types: ["Psychic"], dex: 97 },
  { id: "drowzee", name: "Drowzee", types: ["Psychic"], dex: 96 },
  { id: "krabby", name: "Krabby", types: ["Water"], dex: 98 },
  { id: "kingler", name: "Kingler", types: ["Water"], dex: 99 },
  { id: "voltorb", name: "Voltorb", types: ["Electric"], dex: 100 },
  { id: "electrode", name: "Electrode", types: ["Electric"], dex: 101 },
  { id: "exeggcute", name: "Exeggcute", types: ["Grass", "Psychic"], dex: 102 },
  { id: "exeggutor", name: "Exeggutor", types: ["Grass", "Psychic"], dex: 103 },
  { id: "cubone", name: "Cubone", types: ["Ground"], dex: 104 },
  { id: "marowak", name: "Marowak", types: ["Ground"], dex: 105 },
  { id: "hitmonlee", name: "Hitmonlee", types: ["Fighting"], dex: 106 },
  { id: "hitmonchan", name: "Hitmonchan", types: ["Fighting"], dex: 107 },
  { id: "lickitung", name: "Lickitung", types: ["Normal"], dex: 108 },
  { id: "koffing", name: "Koffing", types: ["Poison"], dex: 109 },
  { id: "weezing", name: "Weezing", types: ["Poison"], dex: 110 },
  { id: "rhyhorn", name: "Rhyhorn", types: ["Ground", "Rock"], dex: 111 },
  { id: "rhydon", name: "Rhydon", types: ["Ground", "Rock"], dex: 112 },
  { id: "chansey", name: "Chansey", types: ["Normal"], dex: 113 },
  { id: "tangela", name: "Tangela", types: ["Grass"], dex: 114 },
  { id: "kangaskhan", name: "Kangaskhan", types: ["Normal"], dex: 115 },
  { id: "horsea", name: "Horsea", types: ["Water"], dex: 116 },
  { id: "seadra", name: "Seadra", types: ["Water"], dex: 117 },
  { id: "goldeen", name: "Goldeen", types: ["Water"], dex: 118 },
  { id: "seaking", name: "Seaking", types: ["Water"], dex: 119 },
  { id: "staryu", name: "Staryu", types: ["Water"], dex: 120 },
  { id: "starmie", name: "Starmie", types: ["Water", "Psychic"], dex: 121 },
  { id: "mr-mime", name: "Mr. Mime", types: ["Psychic"], dex: 122 },
  { id: "scyther", name: "Scyther", types: ["Bug", "Flying"], dex: 123 },
  { id: "jynx", name: "Jynx", types: ["Ice", "Psychic"], dex: 124 },
  { id: "electabuzz", name: "Electabuzz", types: ["Electric"], dex: 125 },
  { id: "magmar", name: "Magmar", types: ["Fire"], dex: 126 },
  { id: "pinsir", name: "Pinsir", types: ["Bug"], dex: 127 },
  { id: "tauros", name: "Tauros", types: ["Normal"], dex: 128 },
  { id: "magikarp", name: "Magikarp", types: ["Water"], dex: 129 },
  { id: "gyarados", name: "Gyarados", types: ["Water", "Flying"], dex: 130 },
  { id: "lapras", name: "Lapras", types: ["Water", "Ice"], dex: 131 },
  { id: "ditto", name: "Ditto", types: ["Normal"], dex: 132 },
  { id: "eevee", name: "Eevee", types: ["Normal"], dex: 133 },
  { id: "vaporeon", name: "Vaporeon", types: ["Water"], dex: 134 },
  { id: "jolteon", name: "Jolteon", types: ["Electric"], dex: 135 },
  { id: "flareon", name: "Flareon", types: ["Fire"], dex: 136 },
  { id: "porygon", name: "Porygon", types: ["Normal"], dex: 137 },
  { id: "omanyte", name: "Omanyte", types: ["Water", "Rock"], dex: 138 },
  { id: "omastar", name: "Omastar", types: ["Water", "Rock"], dex: 139 },
  { id: "kabuto", name: "Kabuto", types: ["Water", "Rock"], dex: 140 },
  { id: "kabutops", name: "Kabutops", types: ["Water", "Rock"], dex: 141 },
  { id: "aerodactyl", name: "Aerodactyl", types: ["Rock", "Flying"], dex: 142 },
  { id: "snorlax", name: "Snorlax", types: ["Normal"], dex: 143 },
  { id: "articuno", name: "Articuno", types: ["Ice", "Flying"], dex: 144 },
  { id: "zapdos", name: "Zapdos", types: ["Electric", "Flying"], dex: 145 },
  { id: "moltres", name: "Moltres", types: ["Fire", "Flying"], dex: 146 },
  { id: "dratini", name: "Dratini", types: ["Dragon"], dex: 147 },
  { id: "dragonair", name: "Dragonair", types: ["Dragon"], dex: 148 },
  { id: "dragonite", name: "Dragonite", types: ["Dragon", "Flying"], dex: 149 },
  { id: "mewtwo", name: "Mewtwo", types: ["Psychic"], dex: 150 },
  { id: "mew", name: "Mew", types: ["Psychic"], dex: 151 },
];

export default function TeamBuilder() {
  const [selectedTeam, setSelectedTeam] = useState<Pokemon[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredPokemon = POKEMON_LIST.filter((pokemon) =>
    pokemon.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const togglePokemon = (pokemon: Pokemon) => {
    const isSelected = selectedTeam.some((p) => p.id === pokemon.id);
    if (isSelected) {
      setSelectedTeam(selectedTeam.filter((p) => p.id !== pokemon.id));
    } else if (selectedTeam.length < 6) {
      setSelectedTeam([...selectedTeam, pokemon]);
    }
  };

  const isSelected = (pokemon: Pokemon) =>
    selectedTeam.some((p) => p.id === pokemon.id);

  const removeFromTeam = (pokemon: Pokemon) => {
    setSelectedTeam(selectedTeam.filter((p) => p.id !== pokemon.id));
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-teal-900 to-teal-950 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-bold text-white text-center mb-2">
          Team Builder
        </h1>
        <p className="text-teal-200 text-center text-lg mb-8">
          Build your Pokemon Go team - select up to 6 Pokemon
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2 bg-white/10 backdrop-blur-md">
            <CardHeader className="flex-col items-start px-6 pt-6">
              <p className="text-xl font-bold text-white">Select Pokemon</p>
              <Input
                placeholder="Search Pokemon..."
                value={searchQuery}
                onValueChange={setSearchQuery}
                className="mt-4 max-w-md"
                variant="bordered"
                classNames={{
                  input: "text-white",
                  inputWrapper: "border-teal-400 hover:border-teal-300",
                }}
              />
            </CardHeader>
            <CardBody>
              <ScrollShadow className="h-[500px] pr-2">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {filteredPokemon.map((pokemon) => (
                    <Card
                      key={pokemon.id}
                      isPressable
                      onPress={() => togglePokemon(pokemon)}
                      className={`transition-all ${
                        isSelected(pokemon)
                          ? "ring-4 ring-teal-400 bg-teal-500/20"
                          : "bg-white/5 hover:bg-white/10"
                      }`}
                    >
                      <CardBody className="p-3">
                        <div className="flex flex-col items-center">
                          <SpeciesAvatar
                            name={pokemon.name}
                            types={pokemon.types}
                            size="lg"
                            className="mb-2"
                          />
                          <p className="text-white text-sm font-medium text-center">
                            {pokemon.name}
                          </p>
                          <div className="flex gap-1 mt-1 flex-wrap justify-center">
                            {pokemon.types.map((type) => (
                              <Chip
                                key={type}
                                size="sm"
                                className={`${TYPE_COLORS[type]} text-white text-xs`}
                              >
                                {type}
                              </Chip>
                            ))}
                          </div>
                        </div>
                      </CardBody>
                    </Card>
                  ))}
                </div>
              </ScrollShadow>
            </CardBody>
          </Card>

          <Card className="bg-white/10 backdrop-blur-md h-fit sticky top-4">
            <CardHeader className="flex-col items-start px-6 pt-6">
              <div className="flex items-center gap-3">
                <p className="text-xl font-bold text-white">Your Team</p>
                <Badge
                  content={selectedTeam.length}
                  color={
                    selectedTeam.length === 6 ? "success" : "warning"
                  }
                  variant="solid"
                >
                  <div className="w-4" />
                </Badge>
              </div>
              <p className="text-teal-200 text-sm mt-1">
                {selectedTeam.length}/6 Pokemon selected
              </p>
            </CardHeader>
            <CardBody>
              {selectedTeam.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-teal-300 text-lg">No Pokemon selected</p>
                  <p className="text-teal-400 text-sm mt-2">
                    Click on Pokemon to add them to your team
                  </p>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {selectedTeam.map((pokemon, index) => (
                    <Card
                      key={pokemon.id}
                      className="bg-white/10"
                    >
                      <CardBody className="p-3 flex flex-row items-center gap-3">
                        <span className="text-teal-300 font-bold w-6">
                          {index + 1}
                        </span>
                        <SpeciesAvatar name={pokemon.name} types={pokemon.types} size="md" />
                        <div className="flex-1">
                          <p className="text-white font-medium">
                            {pokemon.name}
                          </p>
                          <div className="flex gap-1 mt-1">
                            {pokemon.types.map((type) => (
                              <Chip
                                key={type}
                                size="sm"
                                className={`${TYPE_COLORS[type]} text-white text-xs`}
                              >
                                {type}
                              </Chip>
                            ))}
                          </div>
                        </div>
                        <Button
                          isIconOnly
                          size="sm"
                          variant="light"
                          onPress={() => removeFromTeam(pokemon)}
                          className="text-red-400 hover:text-red-300"
                        >
                          ✕
                        </Button>
                      </CardBody>
                    </Card>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </main>
  );
}
