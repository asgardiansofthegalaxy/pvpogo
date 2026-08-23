from django.core.validators import RegexValidator
from django.db import models

stats_validator = RegexValidator(
    regex=r'^\d+,\d+,\d+$',
    message="Stats must be in the format 'attack,defense,stamina' with integers."
)

class PokedexEntry(models.Model):
    dex_number = models.IntegerField()
    species_name = models.CharField(max_length=100)
    # species_id, not dex_number, is what uniquely identifies an entry:
    # regional and alternate forms share a dex number.
    species_id = models.CharField(max_length=100, unique=True)

    #Fields from PokemonFamily
    parent = models.CharField(max_length=100, null=True, blank=True)
    evolutions = models.JSONField(default=list, blank=True)

    types = models.JSONField(default=list)
    base_stats = models.CharField(max_length=50, validators=[stats_validator], default="0,0,0")
    tags = models.JSONField(default=list, blank=True)
    fast_moves = models.JSONField(default=list)
    charged_moves = models.JSONField(default=list)
    buddy_distance = models.IntegerField()
    third_move_cost = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.species_name} (Dex: {self.dex_number})"
    

class Move(models.Model):
    move_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    move_type = models.JSONField(default=list)
    is_fast = models.BooleanField(default=False)
    power = models.IntegerField()
    energy = models.IntegerField()
    energy_gain = models.IntegerField()
    cooldown = models.IntegerField()
    buff = models.JSONField(default=None, null=True, blank=True)  # Allow null, blank, and default=None
    archetype =  models.CharField(max_length=50)

    def __str__(self):
        return self.name
