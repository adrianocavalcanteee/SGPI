from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import RegistroHora, Parada

@receiver([post_save, post_delete], sender=RegistroHora)
def atualizar_totais_por_hora(sender, instance, **kwargs):
    instance.registro.recalc_totais()

@receiver([post_save, post_delete], sender=Parada)
def atualizar_totais_por_parada(sender, instance, **kwargs):
    instance.registro.recalc_totais()
