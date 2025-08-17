from django.db import models
from django.contrib.auth.models import User


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
        ('1/especial', '1/Especial'),
        ('2/especial', '2/Especial'),
        ('3/especial', '3/Especial'),
    ]

    linha = models.ForeignKey(LinhaProducao, on_delete=models.CASCADE, related_name="registros")
    data = models.DateField()
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES)

    quantidade_produzida = models.PositiveIntegerField()
    quantidade_defeituosa = models.PositiveIntegerField(default=0)
    tempo_parado = models.PositiveIntegerField(default=0, help_text="Tempo parado em minutos")
    motivo_parada = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)  
    atualizado_em = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"{self.linha.nome} - {self.data} - {self.turno}"

    @property
    def taxa_defeitos(self):
        if self.quantidade_produzida == 0:
            return 0
        return (self.quantidade_defeituosa / self.quantidade_produzida) * 100


class RegistroHora(models.Model):
    registro = models.ForeignKey(RegistroProducao, on_delete=models.CASCADE, related_name="registros_hora")
    hora = models.TimeField()
    quantidade_produzida = models.PositiveIntegerField()
    quantidade_defeituosa = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.registro} - {self.hora}"

    @property
    def taxa_defeitos(self):
        if self.quantidade_produzida == 0:
            return 0
        return (self.quantidade_defeituosa / self.quantidade_produzida) * 100


class Parada(models.Model):
    registro = models.ForeignKey(RegistroProducao, on_delete=models.CASCADE, related_name="paradas")
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    duracao = models.PositiveIntegerField(help_text="Duração em minutos")
    motivo = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Parada {self.hora_inicio} - {self.hora_fim} ({self.duracao} min)"
