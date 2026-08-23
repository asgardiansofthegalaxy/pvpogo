import json
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from app.models import PokedexEntry, Move

import pypogo


# Resolve the bundled Game Master exports off the installed pypogo package, so
# the command works regardless of the directory it is invoked from.
GAME_MASTER_DIR = os.path.join(os.path.dirname(pypogo.__file__), 'game_master')


class Command(BaseCommand):
    help = 'Load Pokémon and Move data from JSON into the database'

    POKEMON_JSON_PATH = os.path.join(GAME_MASTER_DIR, 'pokemon.json')
    MOVES_JSON_PATH = os.path.join(GAME_MASTER_DIR, 'moves.json')

    def add_arguments(self, parser):
        parser.add_argument('--pokemon-json', type=str, default=self.POKEMON_JSON_PATH, help=f'The path to the JSON file containing the Pokémon data (default: {self.POKEMON_JSON_PATH})')
        parser.add_argument('--moves-json', type=str, default=self.MOVES_JSON_PATH, help=f'The path to the JSON file containing the Moves data (default: {self.MOVES_JSON_PATH})')

    def handle(self, *args, **options):
        pokemon_created, pokemon_updated, pokemon_failed = 0, 0, 0
        moves_created, moves_updated, moves_failed = 0, 0, 0

        # argparse turns --pokemon-json into the "pokemon_json" key; indexing
        # options by the default *path* raised KeyError on every run.
        with open(options['pokemon_json'], 'r') as file:
            data = json.load(file)
            self.stdout.write(self.style.SUCCESS('Starting to load Pokémon data...'))
            with transaction.atomic():
                for pokemon_name, poke_data in data.items():
                    # Format the stats in the required 'attack,defense,stamina' format
                    formatted_stats = "{},{},{}".format(
                        poke_data['base_stats']['attack'],
                        poke_data['base_stats']['defense'],
                        poke_data['base_stats']['stamina']
                    )
                    
                    # Use update_or_create to handle both new entries and updates to existing entries
                    try:
                        # Keyed on species_id, not dex_number: regional and
                        # alternate forms share a dex number (stunfisk and
                        # stunfisk_galarian are both 618), so keying on it
                        # collapsed 1283 entries down to 1005.
                        pokedex_entry, created = PokedexEntry.objects.update_or_create(
                            species_id=poke_data['species_id'],
                            defaults={
                                'dex_number': poke_data['dex_number'],
                                'species_name': poke_data['species_name'],
                                'parent': poke_data['family']['parent'] if poke_data['family']['parent'] else '',
                                'evolutions': poke_data['family']['evolutions'],
                                'types': poke_data['types'],
                                'base_stats': formatted_stats,
                                'tags': poke_data['tags'],
                                'buddy_distance': poke_data['buddy_distance'],
                                'third_move_cost': poke_data.get('third_move_cost', None),
                                'fast_moves': poke_data['fast_moves'],
                                'charged_moves': poke_data['charged_moves']
                            }
                        )
                        if created:
                            pokemon_created += 1
                            self.stdout.write(self.style.SUCCESS(f"Successfully added Pokedex entry: {pokedex_entry.species_name}"))
                        else:
                            pokemon_updated += 1
                            self.stdout.write(self.style.WARNING(f"Updated existing Pokedex entry: {pokedex_entry.species_name}"))
                    except Exception as e:
                        pokemon_failed += 1
                        self.stdout.write(f"Unexpected error while updating/creating Pokedex entry: {e}")

            self.stdout.write(self.style.SUCCESS('Successfully loaded Pokémon data into the database'))


        with open(options['moves_json'], 'r') as file:
            moves_data = json.load(file)
            self.stdout.write(self.style.SUCCESS('Starting to load Move data...'))
            with transaction.atomic():
                for move_name, move_attrs in moves_data.items():
                    # buff is a nullable JSONField, so a null in the JSON is
                    # stored as-is rather than as a placeholder string.
                    buff = move_attrs['buff']

                    # Since move_type is a string in your JSON, but your model expects a list (JSONField)
                    # Convert move_type to a list, assuming it always contains a single type
                    move_type = [move_attrs['move_type']]
                    try:
                        move, created = Move.objects.update_or_create(
                        move_id=move_attrs['move_id'],
                            defaults={
                                'name': move_attrs['name'],
                                'move_type': move_type,
                                'is_fast': move_attrs['is_fast'],
                                'power': move_attrs['power'],
                                'energy': move_attrs['energy'],
                                'energy_gain': move_attrs['energy_gain'],
                                'cooldown': move_attrs['cooldown'],
                                'buff': buff,
                                'archetype': move_attrs['archetype']
                            }
                        )
                        if created:
                            moves_created += 1
                            self.stdout.write(self.style.SUCCESS(f"Successfully added move: {move.name}"))
                        else:
                            moves_updated += 1
                            self.stdout.write(self.style.WARNING(f"Updated existing move: {move.name}"))
                    except Exception as e:
                        moves_failed += 1
                        self.stdout.write(f"Unexpected error while updating/creating Move: {e}")

        self.stdout.write(self.style.SUCCESS('Successfully loaded Move data into the database'))

        # Log summary
        self.stdout.write(self.style.SUCCESS(f"Pokémon entries created: {pokemon_created}, updated: {pokemon_updated}, failed: {pokemon_failed}"))
        self.stdout.write(self.style.SUCCESS(f"Moves created: {moves_created}, updated: {moves_updated}, failed: {moves_failed}"))
