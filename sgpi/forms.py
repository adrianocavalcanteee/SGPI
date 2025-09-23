# sgpi/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import LinhaProducao, RegistroProducao, RegistroHora, Parada
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

class LinhaProducaoForm(forms.ModelForm):
    class Meta:
        model = LinhaProducao
        fields = ["nome", "setor", "capacidade_nominal"]

class RegistroProducaoForm(forms.ModelForm):
    class Meta:
        model = RegistroProducao
        fields = [
            "linha", "data", "turno",
            "finalizada"
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "finalizada": forms.HiddenInput(),
        }
    RegistroHoraFormSet = inlineformset_factory(
    RegistroProducao,
    RegistroHora,
    fields=["hora_inicio", "hora_fim", "quantidade_produzida", "quantidade_defeituosa"],
    extra=1,
    can_delete=True
)

    def clean(self):
        cleaned = super().clean()
        data = cleaned.get("data")
        if data and data > timezone.now().date():
            raise ValidationError("A data do registro não pode ser no futuro.")
        
        qtd = cleaned.get("quantidade_produzida")
        defe = cleaned.get("quantidade_defeituosa")
        if qtd is not None and defe is not None and defe > qtd:
            raise ValidationError("Quantidade defeituosa não pode ser maior que a produzida.")
        return cleaned


class RegistroHoraForm(forms.ModelForm):
    class Meta:
        model = RegistroHora
        fields = ["hora_inicio", "hora_fim", "quantidade_produzida", "quantidade_defeituosa"]
        widgets = {
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fim": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned = super().clean()
        hi = cleaned.get("hora_inicio")
        hf = cleaned.get("hora_fim")
        qtd = cleaned.get("quantidade_produzida")
        defe = cleaned.get("quantidade_defeituosa")

        if hi and hf and hi == hf:
            raise ValidationError("A hora final deve ser diferente da hora inicial.")

        if qtd is not None and defe is not None and defe > qtd:
            raise ValidationError("Quantidade defeituosa não pode ser maior que a produzida.")

        return cleaned


class ParadaForm(forms.ModelForm):
    class Meta:
        model = Parada
        fields = ["hora_inicio", "hora_fim", "motivo"]
        widgets = {
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fim": forms.TimeInput(attrs={"type": "time"}),
            "motivo": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        hi = cleaned.get("hora_inicio")
        hf = cleaned.get("hora_fim")
        if hi and hf and hi == hf:
            raise ValidationError("A hora final deve ser diferente da hora inicial.")
        return cleaned


# Formsets inline para usar nas views/templates
RegistroHoraFormSet = inlineformset_factory(
    RegistroProducao,
    RegistroHora,
    form=RegistroHoraForm,
    extra=1,
    can_delete=True,
)

ParadaFormSet = inlineformset_factory(
    RegistroProducao,
    Parada,
    form=ParadaForm,
    extra=1,
    can_delete=True,
)


# forms dos users
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="Nome", required=False)
    last_name = forms.CharField(label="Sobrenome", required=False)
    is_staff = forms.BooleanField(label="Pode acessar o admin?", required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_staff", "password1", "password2")


class CustomUserChangeForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="Nome", required=False)
    last_name = forms.CharField(label="Sobrenome", required=False)
    is_staff = forms.BooleanField(label="Pode acessar o admin?", required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
