# sgpi/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import (
    LinhaProducao,
    RegistroProducao,
    RegistroHora,
    Parada,
    PermissaoSetorUsuario,   
)

# -----------------------
# Linhas
# -----------------------
class LinhaProducaoForm(forms.ModelForm):
    class Meta:
        model = LinhaProducao
        fields = ["nome", "setor", "capacidade_nominal"]

# -----------------------
# Registro (pai)
# -----------------------
class RegistroProducaoForm(forms.ModelForm):
    """
    Restringe a escolha de LINHA aos SETORES permitidos ao usuário.
    Não restringe turno (fica livre).
    """
    class Meta:
        model = RegistroProducao
        fields = ["linha", "data", "turno", "finalizada"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "finalizada": forms.HiddenInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated and not user.is_superuser:
            setores = list(
                PermissaoSetorUsuario.objects.filter(usuario=user)
                .values_list("setor", flat=True)
            )
            # filtra linhas pelos setores permitidos
            self.fields["linha"].queryset = self.fields["linha"].queryset.filter(setor__in=setores)

    def clean(self):
        cleaned = super().clean()
        data = cleaned.get("data")
        linha = cleaned.get("linha")

        if data and data > timezone.now().date():
            raise ValidationError("A data do registro não pode ser no futuro.")

        user = getattr(self, "user", None)
        if user and user.is_authenticated and not user.is_superuser:
            if not linha:
                raise ValidationError("Selecione uma linha válida.")
            # valida setor permitido
            setor = linha.setor
            ok = PermissaoSetorUsuario.objects.filter(usuario=user, setor=setor).exists()
            if not ok:
                raise ValidationError("Você não tem permissão para registrar neste setor.")
        return cleaned

# -----------------------
# Filhos
# -----------------------
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

# -----------------------
# Formsets filhos
# -----------------------
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

# -----------------------
# Users
# -----------------------
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

# -----------------------
# Formset de permissões por SETOR (para a tela Editar Usuário)
# -----------------------

# Para UX melhor, criamos um ModelForm que converte setor em Choice a partir dos setores existentes.
class PermissaoSetorUsuarioForm(forms.ModelForm):
    setor = forms.ChoiceField(label="Setor")

    class Meta:
        model = PermissaoSetorUsuario
        fields = ["setor"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setores = (
            LinhaProducao.objects
            .exclude(setor__isnull=True)
            .exclude(setor__exact="")
            .order_by("setor")
            .values_list("setor", flat=True)
            .distinct()
        )
        choices = [("", "— Selecione —")] + [(s, s) for s in setores]
        self.fields["setor"].choices = [(s, s) for s in setores]

PermissaoSetorUsuarioFormSet = inlineformset_factory(
    parent_model=get_user_model(),
    model=PermissaoSetorUsuario,
    form=PermissaoSetorUsuarioForm,
    extra=0,
    can_delete=True,
)
