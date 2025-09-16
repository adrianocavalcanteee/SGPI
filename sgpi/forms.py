# sgpi/forms.py
from django import forms
from .models import LinhaProducao, RegistroProducao
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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


#forms dos users
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
