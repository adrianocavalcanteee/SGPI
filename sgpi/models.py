from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum


class LinhaProducao(models.Model):
    nome = models.CharField(max_length=100)
    setor = models.CharField(max_length=100, blank=True, null=True)

    capacidade_nominal = models.PositiveIntegerField(
        help_text="Capacidade nominal em unidades por hora"
    )

    def __str__(self):
        return self.nome



class RegistroProducao(models.Model):
    TURNO_CHOICES = [
        ("1/especial", "1/Especial"),
        ("2/especial", "2/Especial"),
        ("3/especial", "3/Especial"),
    ]

    linha = models.ForeignKey(
        LinhaProducao, on_delete=models.CASCADE, related_name="registros"
    )
    data = models.DateField()
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES)

    
    quantidade_produzida = models.PositiveIntegerField(default=0)
    quantidade_defeituosa = models.PositiveIntegerField(default=0)
    tempo_parado = models.PositiveIntegerField(
        default=0, help_text="Tempo parado em minutos"
    )
    

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    finalizada = models.BooleanField(default=False)
    finalizada_em = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.linha.nome} - {self.data} - {self.turno}"

    @property
    def taxa_defeitos(self):
        if self.quantidade_produzida == 0:
            return 0
        return (self.quantidade_defeituosa / self.quantidade_produzida) * 100

    
    def recalc_totais(self, save=True):
        agg_horas = self.registros_hora.aggregate(
            prod=Sum("quantidade_produzida"),
            defe=Sum("quantidade_defeituosa"),
        )
        agg_paradas = self.paradas.aggregate(parado=Sum("duracao"))

        self.quantidade_produzida = agg_horas["prod"] or 0
        self.quantidade_defeituosa = agg_horas["defe"] or 0
        self.tempo_parado = agg_paradas["parado"] or 0

        if save:
            self.save(
                update_fields=[
                    "quantidade_produzida",
                    "quantidade_defeituosa",
                    "tempo_parado",
                    "atualizado_em",
                ]
            )

    class Meta:
        verbose_name = "Registro de produção"
        verbose_name_plural = "Registros de producão"
        unique_together = [("linha", "data", "turno")]  
    def finalizar(self, save=True):
        
        self.recalc_totais(save=False)
        self.finalizada = True
        self.finalizada_em = timezone.now()
        if save:
            self.save(update_fields=[
                "quantidade_produzida", "quantidade_defeituosa",
                "tempo_parado", "finalizada", "finalizada_em", "atualizado_em"
            ])

    def reabrir(self, save=True):
        self.finalizada = False
        self.finalizada_em = None
        if save:
            self.save(update_fields=["finalizada", "finalizada_em", "atualizado_em"])

   
    @property
    def resumo_total_produzido(self):
        return self.quantidade_produzida

    @property
    def resumo_total_defeituoso(self):
        return self.quantidade_defeituosa

    @property
    def resumo_tempo_parado_min(self):
        return self.tempo_parado

    @property
    def resumo_taxa_defeitos_pct(self):
        return round(self.taxa_defeitos, 2)


class RegistroHora(models.Model):
    registro = models.ForeignKey(
        RegistroProducao, on_delete=models.CASCADE, related_name="registros_hora"
    )
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    
    quantidade_produzida = models.PositiveIntegerField(default=0)
    quantidade_defeituosa = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.registro} - {self.hora_inicio} às {self.hora_fim}"

    def clean(self):
        if self.hora_fim == self.hora_inicio:
            raise ValidationError("A hora final deve ser diferente da hora inicial.")

    @property
    def minutos_intervalo(self) -> int:
        dt_ini = datetime.combine(self.registro.data, self.hora_inicio)
        dt_fim = datetime.combine(self.registro.data, self.hora_fim)
        if dt_fim <= dt_ini:
            dt_fim += timedelta(days=1)
        return int((dt_fim - dt_ini).total_seconds() // 60)

    @property
    def taxa_defeitos(self):
        if self.quantidade_produzida == 0:
            return 0
        return (self.quantidade_defeituosa / self.quantidade_produzida) * 100

    class Meta:
        ordering = ("hora_inicio",)


class Parada(models.Model):
    registro = models.ForeignKey(
        RegistroProducao, on_delete=models.CASCADE, related_name="paradas"
    )
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    duracao = models.PositiveIntegerField(
        default=0, help_text="Duração em minutos (calculada automaticamente)"
    )
    motivo = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Parada {self.hora_inicio} - {self.hora_fim} ({self.duracao} min)"

    def clean(self):
        
        if self.hora_fim == self.hora_inicio:
            raise ValidationError("A hora final deve ser diferente da hora inicial.")

    def save(self, *args, **kwargs):
        
        dt_ini = datetime.combine(self.registro.data, self.hora_inicio)
        dt_fim = datetime.combine(self.registro.data, self.hora_fim)
        if dt_fim <= dt_ini:
            dt_fim += timedelta(days=1)
        self.duracao = int((dt_fim - dt_ini).total_seconds() // 60)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ("hora_inicio",)
        verbose_name = "Parada"
        verbose_name_plural = "Paradas"
