# sgpi/forms.py
from django import forms
from .models import LinhaProducao, RegistroProducao

class LinhaProducaoForm(forms.ModelForm):
    class Meta:
        model = LinhaProducao
        fields = ["nome", "setor", "capacidade_nominal"]

class RegistroProducaoForm(forms.ModelForm):
    class Meta:
        model = RegistroProducao
        fields = [
            "linha", "data", "turno",
            "quantidade_produzida", "quantidade_defeituosa",
            "tempo_parado", "motivo_parada"
        ]
        widgets = {"data": forms.DateInput(attrs={"type": "date"})}
