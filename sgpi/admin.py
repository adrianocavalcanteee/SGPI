from django.contrib import admin
from .models import LinhaProducao, RegistroProducao, RegistroHora

@admin.register(LinhaProducao)
class LinhaProducaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'setor', 'capacidade_nominal')
    search_fields = ('nome', 'setor')


@admin.register(RegistroProducao)
class RegistroProducaoAdmin(admin.ModelAdmin):
    list_display = ('linha', 'data', 'turno', 'quantidade_produzida', 
                    'quantidade_defeituosa', 'tempo_parado',)
    list_filter = ('linha', 'turno', 'data')
    search_fields = ('linha__nome', 'motivo_parada')
    date_hierarchy = 'data'


@admin.register(RegistroHora)
class RegitroHora(admin.ModelAdmin):
    list_display = ('registro', 'hora', 'quantidade_produzida','quantidade_defeituosa',)
    

