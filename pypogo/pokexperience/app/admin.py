from django.contrib import admin

from .models import PokedexEntry, Move

admin.site.register(PokedexEntry)
admin.site.register(Move)
