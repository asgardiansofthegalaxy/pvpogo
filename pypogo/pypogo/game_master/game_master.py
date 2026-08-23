import json
import os
import re
from typing import Dict, List, Optional

from pypogo.buff import MoveBuff
from pypogo.constants import MAX_IV, MAX_LEVEL
from pypogo.moves import Move
from pypogo.pokedex import PokedexEntry, PokemonFamily
from pypogo.pokemon import PvpPokemon
from pypogo.poketypes import PokeType
from pypogo.stats import Stats

CWD = os.path.dirname(os.path.abspath(__file__))


MOVE_PATTERN = r"COMBAT_V\d{4}_MOVE_([A-Z_]+?)(?:_FAST)?$"
POKEMON_PATTERN = r"V\d+_POKEMON_(PORYGON2|PIKACHU|[A-Z]+(?:_(?!NORMAL$|COPY_|FALL_|ADVENTURE_HAT_|FLYING_|COSTUME_|GOFEST_|GOTOUR_|JEJU|KARIYUSHI|POP_STAR|ROCK_STAR|SUMMER_|TSHIRT_|VS_|WCS_|WINTER_)[A-Z]+)?)$"

PATTERNS = {
    "move": re.compile(MOVE_PATTERN),
    "pokemon": re.compile(POKEMON_PATTERN),
}


class GameMaster:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if not self.__initialized:
            gm_data = self._load_gm_data()
            grouped_keys = self._get_grouped_keys(gm_data)
            self._moves = self._load_moves(grouped_keys["move"])
            self._pokedex_pokemon = self._load_pokedex_pokemon(grouped_keys["pokemon"])
            self.__initialized = True

    def list_pokemon(self, league=None):
        raise NotImplementedError

    def get_pokemon(
        self,
        species_id: "str",
        fast_move_id: Optional[str] = None,
        charged_move_ids: Optional[List[str]] = None,
        level: float = MAX_LEVEL,
        ivs: Stats = Stats(MAX_IV, MAX_IV, MAX_IV),
    ) -> PvpPokemon:
        pokedex_entry = self._pokedex_pokemon[species_id]
        if fast_move_id:
            fast_move = self._moves[fast_move_id]
        else:
            # Pick the first available move
            fast_move = self._moves[pokedex_entry.fast_moves[0]]

        if charged_move_ids:
            if len(charged_move_ids) > 2:
                raise ValueError("Only 2 charged moves are allowed")
            charged_moves = [self._moves[move_id] for move_id in charged_move_ids]
        else:
            charged_moves = [
                self._moves[move_id] for move_id in pokedex_entry.charged_moves[:2]
            ]

        return PvpPokemon(
            pdex_mon=pokedex_entry,
            level=level,
            ivs=ivs,
            fast_move=fast_move,
            charged_moves=charged_moves,
        )

    def list_moves(self):
        raise NotImplementedError

    def get_move(self, move_id: int):
        raise NotImplementedError

    @staticmethod
    def _load_gm_data() -> dict:
        with open(os.path.join(CWD, "gm_latest.json"), "r") as fp:
            gm_data = json.load(fp)

        return gm_data

    @staticmethod
    def _get_grouped_keys(gm_data: dict) -> dict:
        grouped_keys: Dict[str, list] = {pattern: [] for pattern in PATTERNS}

        def match_key(key):
            for pattern_name, pattern_regex in PATTERNS.items():
                if pattern_regex.match(key):
                    return pattern_name
            return None

        for data in gm_data:
            key = data["templateId"]
            matched_pattern = match_key(key)
            if matched_pattern:
                grouped_keys[matched_pattern].append(data)
                pass

        return grouped_keys

    @staticmethod
    def _load_moves(move_data: dict) -> Dict[str, Move]:
        moves = {}

        for item in move_data:

            move_data = item["data"]["combatMove"]

            move_id_raw = move_data["uniqueId"]
            move_id = move_id_raw.replace("_FAST", "")
            name = move_data["uniqueId"].replace("_", " ").title()
            move_type = PokeType(move_data["type"].replace("POKEMON_TYPE_", "").lower())
            is_fast = "_FAST" in move_id_raw
            power = move_data.get("power", 0)
            raw_energy = move_data.get("energyDelta", 0)
            energy_gain = raw_energy if raw_energy > 0 else 0
            energy = abs(raw_energy) if raw_energy < 0 else 0
            cooldown = 500 * (move_data.get("durationTurns", 0) + 1)

            # Buff
            buff = None
            if "buffs" in move_data:
                chance = move_data["buffs"]["buffActivationChance"]
                atk_buff_self = move_data["buffs"].get(
                    "attackerAttackStatStageChange", 0
                )
                def_buff_self = move_data["buffs"].get(
                    "attackerDefenseStatStageChange", 0
                )
                atk_buff_opponent = move_data["buffs"].get(
                    "targetAttackStatStageChange", 0
                )
                def_buff_opponent = move_data["buffs"].get(
                    "targetDefenseStatStageChange", 0
                )
                buff = MoveBuff(
                    chance=chance,
                    atk_buff_self=atk_buff_self,
                    def_buff_self=def_buff_self,
                    atk_buff_opponent=atk_buff_opponent,
                    def_buff_opponent=def_buff_opponent,
                )

            moves[move_id] = Move(
                move_id=move_id,
                name=name,
                move_type=move_type,
                is_fast=is_fast,
                power=power,
                energy=energy,
                energy_gain=energy_gain,
                cooldown=cooldown,
                buff=buff,
            )

        return moves

    @staticmethod
    def _load_pokedex_pokemon(pokemon_data: dict) -> Dict[str, PokedexEntry]:

        pokemon = {}

        for item in pokemon_data:

            template_id = item["templateId"]  # i.e 'V0001_POKEMON_BULBASAUR'
            dex_str = template_id.split("_")[0]
            dex_number = int(dex_str.strip("V"))
            pokemon_data = item["data"].get("pokemonSettings")

            if not pokemon_data:
                continue

            species_name = pokemon_data["pokemonId"].title()
            species_id = re.sub(r"V\d{4}_POKEMON_", "", template_id).lower()

            # Family
            family_id = pokemon_data["familyId"]
            parent = pokemon_data.get("parentPokemonId")

            # Evolutions
            evolutions = []
            for evolution_data in pokemon_data.get("evolutionBranch", []):
                evolution = evolution_data.get("evolution")
                if evolution:
                    evolutions.append(evolution)
            family = PokemonFamily(family_id, parent, evolutions)

            # Types
            types = [PokeType("none"), PokeType("none")]
            types[0] = PokeType(
                pokemon_data["type"].replace("POKEMON_TYPE_", "").lower()
            )
            if "type2" in pokemon_data:
                types[1] = PokeType(
                    pokemon_data["type2"].replace("POKEMON_TYPE_", "").lower()
                )

            # Stats
            attack = pokemon_data["stats"].get("baseAttack", 0)
            stamina = pokemon_data["stats"].get("baseStamina", 0)
            defense = pokemon_data["stats"].get("baseDefense", 0)
            stats = Stats(attack, defense, stamina)

            # Moves
            fast_moves = [
                move.replace("_FAST", "")
                for move in pokemon_data.get("quickMoves", [])
                + pokemon_data.get("eliteQuickMove", [])
            ]
            charged_moves = pokemon_data.get("cinematicMoves", []) + pokemon_data.get(
                "eliteCinematicMove", []
            )

            # Other
            buddy_distance = pokemon_data["kmBuddyDistance"]
            third_move_cost = pokemon_data["thirdMove"].get("stardustToUnlock")

            pokemon[species_id] = PokedexEntry(
                dex_number=dex_number,
                species_name=species_name,
                species_id=species_id,
                family=family,
                types=types,
                base_stats=stats,
                tags=[],  # TODO
                fast_moves=fast_moves,
                charged_moves=charged_moves,
                buddy_distance=buddy_distance,
                third_move_cost=third_move_cost,
            )

        return pokemon
