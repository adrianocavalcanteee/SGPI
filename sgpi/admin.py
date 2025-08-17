from django.contrib import admin, messages
from .models import LinhaProducao, RegistroProducao, RegistroHora, Parada




@admin.register(LinhaProducao)
class LinhaProducaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "setor", "capacidade_nominal")

class RegistroHoraInline(admin.TabularInline):
    model = RegistroHora
    extra = 1
    fields = ("hora_inicio", "hora_fim", "quantidade_produzida", "quantidade_defeituosa")
    ordering = ("hora_inicio",)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.finalizada:
            return ("hora_inicio", "hora_fim", "quantidade_produzida", "quantidade_defeituosa")
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj):
        return False if (obj and obj.finalizada) else super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False if (obj and obj.finalizada) else super().has_delete_permission(request, obj)


class ParadaInline(admin.TabularInline):
    model = Parada
    extra = 0
    fields = ("hora_inicio", "hora_fim", "duracao", "motivo")
    readonly_fields = ("duracao",)

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        if obj and obj.finalizada:
            return ("hora_inicio", "hora_fim", "duracao", "motivo")
        return tuple(base)

    def has_add_permission(self, request, obj):
        return False if (obj and obj.finalizada) else super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False if (obj and obj.finalizada) else super().has_delete_permission(request, obj)


@admin.register(RegistroProducao)
class RegistroProducaoAdmin(admin.ModelAdmin):
    list_display = (
        "linha", "data", "turno",
        "quantidade_produzida", "quantidade_defeituosa", "tempo_parado",
        "finalizada", "finalizada_em",
    )
    list_filter = ("linha", "turno", "data", "finalizada")
    search_fields = ("linha__nome", "motivo_parada")
    date_hierarchy = "data"
    inlines = [RegistroHoraInline, ParadaInline]


    @admin.display(description="Total produzido (u)")
    def resumo_total_produzido(self, obj: RegistroProducao):
        return obj.resumo_total_produzido

    @admin.display(description="Total defeituoso (u)")
    def resumo_total_defeituoso(self, obj: RegistroProducao):
        return obj.resumo_total_defeituoso

    @admin.display(description="Taxa de defeitos (%)")
    def resumo_taxa_defeitos_pct(self, obj: RegistroProducao):
        return obj.resumo_taxa_defeitos_pct

    @admin.display(description="Tempo parado (min)")
    def resumo_tempo_parado_min(self, obj: RegistroProducao):
        return obj.resumo_tempo_parado_min

    
    base_readonly = ("quantidade_produzida", "quantidade_defeituosa", "tempo_parado")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.finalizada:
            
            return self.base_readonly + (
                "linha", "data", "turno", "motivo_parada", "finalizada", "finalizada_em",
                
                "resumo_total_produzido", "resumo_total_defeituoso",
                "resumo_taxa_defeitos_pct", "resumo_tempo_parado_min",
            )
        
        return self.base_readonly + (
            "resumo_total_produzido", "resumo_total_defeituoso",
            "resumo_taxa_defeitos_pct", "resumo_tempo_parado_min",
        )

    fieldsets = (
        ("Resumo do dia (somente leitura)", {
            "fields": (
                ("resumo_total_produzido", "resumo_total_defeituoso", "resumo_taxa_defeitos_pct"),
                "resumo_tempo_parado_min",
            )
        }),
        ("Dados do registro", {
            "fields": (
                ("linha", "data", "turno"),
                ("quantidade_produzida", "quantidade_defeituosa", "tempo_parado"),
                
                ("finalizada", "finalizada_em"),
            )
        }),
    )

    actions = ["acao_finalizar", "acao_reabrir"]

    @admin.action(description="Finalizar registros selecionados")
    def acao_finalizar(self, request, queryset):
        count = 0
        for reg in queryset:
            if not reg.finalizada:
                reg.finalizar()
                count += 1
        self.message_user(request, f"{count} registro(s) finalizado(s).", level=messages.SUCCESS)

    @admin.action(description="Reabrir registros selecionados")
    def acao_reabrir(self, request, queryset):
        count = 0
        for reg in queryset:
            if reg.finalizada:
                reg.reabrir()
                count += 1
        self.message_user(request, f"{count} registro(s) reaberto(s).", level=messages.WARNING)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalc_totais()
