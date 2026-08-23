from django.contrib import admin

from .models import Move, PokedexEntry

admin.site.register(PokedexEntry)
admin.site.register(Move)
