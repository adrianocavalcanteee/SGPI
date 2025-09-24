# app/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .models import LinhaProducao, RegistroProducao
from .forms import (
    RegistroProducaoForm,
    RegistroHoraFormSet,
    ParadaFormSet,
    CustomUserCreationForm,
    CustomUserChangeForm,
)

# =========================
# Helpers para formsets (sem JS)
# =========================

def _increment_total_forms(post_data, prefix: str):
    """
    Retorna uma cópia de POST com <prefix>-TOTAL_FORMS incrementado (+1).
    Ex.: prefix='hora' -> campo 'hora-TOTAL_FORMS'
    """
    data = post_data.copy()
    key = f"{prefix}-TOTAL_FORMS"
    data[key] = str(int(data.get(key, "0")) + 1)
    return data


def _remove_formset_row(post_data, prefix: str, pressed_value: str):
    """
    Remove uma linha do formset sem JS.

    - Se a linha for inicial (idx < INITIAL_FORMS): marca DELETE=on.
    - Se for extra (idx >= INITIAL_FORMS): reindexa os extras e TOTAL_FORMS -= 1.
    Usa QueryDict.setlist para preservar tipos corretos.
    """
    data = post_data.copy()  # QueryDict mutável
    try:
        # pressed_value exemplo: 'hora-3' -> idx = 3
        idx = int(pressed_value.split("-")[1])
    except Exception:
        return data

    total = int(data.get(f"{prefix}-TOTAL_FORMS", "0"))
    initial = int(data.get(f"{prefix}-INITIAL_FORMS", "0"))

    if idx >= total:
        return data  # índice inválido

    if idx < initial:
        # Linha existente -> marca DELETE (apaga ao salvar)
        data.setlist(f"{prefix}-{idx}-DELETE", ["on"])
        return data

    # Linha nova -> reindexar extras (fecha o buraco) e diminuir TOTAL_FORMS
    for i in range(idx + 1, total):
        old_prefix = f"{prefix}-{i}-"
        new_prefix = f"{prefix}-{i-1}-"

        keys_i = [k for k in data.keys() if k.startswith(old_prefix)]
        for key in keys_i:
            vals = data.getlist(key)                  # lista de valores
            new_key = key.replace(old_prefix, new_prefix, 1)
            data.setlist(new_key, vals)               # escreve corretamente
            try:
                del data[key]                         # remove a chave antiga
            except KeyError:
                pass

    # Remove qualquer chave remanescente do último índice (total - 1)
    last = total - 1
    last_prefix = f"{prefix}-{last}-"
    for k in [k for k in list(data.keys()) if k.startswith(last_prefix)]:
        try:
            del data[k]
        except KeyError:
            pass

    data[f"{prefix}-TOTAL_FORMS"] = str(total - 1)
    return data


# =========================
# Linhas de Produção (CRUD simples)
# =========================

class LinhaProducaoListView(ListView):
    model = LinhaProducao
    template_name = "linhas/lista.html"
    context_object_name = "linhas"


class LinhaProducaoCreateView(CreateView):
    model = LinhaProducao
    template_name = "linhas/form.html"
    fields = ["nome", "setor", "capacidade_nominal"]
    success_url = reverse_lazy("linhas-lista")


class LinhaProducaoUpdateView(UpdateView):
    model = LinhaProducao
    template_name = "linhas/form.html"
    fields = ["nome", "setor", "capacidade_nominal"]
    success_url = reverse_lazy("linhas-lista")


class LinhaProducaoDeleteView(DeleteView):
    model = LinhaProducao
    template_name = "linhas/confirm_delete.html"
    success_url = reverse_lazy("linhas-lista")


# =========================
# Registros de Produção
# =========================

class RegistroProducaoListView(ListView):
    model = RegistroProducao
    template_name = "registros/lista.html"
    context_object_name = "registros"
    ordering = ["-data", "turno"]
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(linha__nome__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registros = context.get("registros") or []
        iterable = getattr(registros, "object_list", registros)

        for registro in iterable:
            try:
                hora_qs = registro.registros_hora.all()
            except Exception:
                hora_qs = []
            total_prod = sum(getattr(h, "quantidade_produzida", 0) or 0 for h in hora_qs)
            total_def = sum(getattr(h, "quantidade_defeituosa", 0) or 0 for h in hora_qs)
            setattr(registro, "total_produzido", total_prod)
            setattr(registro, "total_defeituoso", total_def)

        context["q"] = self.request.GET.get("q", "")
        return context


class RegistroProducaoDetailView(DetailView):
    model = RegistroProducao
    template_name = "registros/detalhes.html"
    context_object_name = "registro"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registro = self.object

        producao_hora = registro.registros_hora.all()
        paradas = registro.paradas.all()

        context["producao_hora"] = producao_hora
        context["paradas"] = paradas
        context["total_produzido"] = sum(h.quantidade_produzida for h in producao_hora)
        context["total_defeituoso"] = sum(h.quantidade_defeituosa for h in producao_hora)
        return context


@login_required
def criar_registro(request):
    if request.method == "POST":
        post_data = request.POST

        # Adicionar linhas (sem JS)
        if "add_hora" in post_data:
            post_data = _increment_total_forms(post_data, "hora")
        if "add_parada" in post_data:
            post_data = _increment_total_forms(post_data, "parada")

        # Remover linhas (−)
        if "rem_hora" in post_data:
            post_data = _remove_formset_row(post_data, "hora", post_data.get("rem_hora"))
        if "rem_parada" in post_data:
            post_data = _remove_formset_row(post_data, "parada", post_data.get("rem_parada"))

        form = RegistroProducaoForm(post_data)
        formset_hora = RegistroHoraFormSet(post_data, prefix="hora")
        formset_parada = ParadaFormSet(post_data, prefix="parada")

        if "salvar" in request.POST and form.is_valid() and formset_hora.is_valid() and formset_parada.is_valid():
            registro = form.save()

            formset_hora.instance = registro
            formset_hora.save()

            formset_parada.instance = registro
            formset_parada.save()

            # Se ainda usa esses agregados no model:
            registro.quantidade_produzida = sum(h.quantidade_produzida for h in registro.registros_hora.all())
            registro.quantidade_defeituosa = sum(h.quantidade_defeituosa for h in registro.registros_hora.all())
            registro.save(update_fields=["quantidade_produzida", "quantidade_defeituosa"])

            messages.success(request, "Registro criado com sucesso.")
            return redirect("registros-detalhes", pk=registro.pk)

        return render(request, "registros/form.html", {
            "form": form,
            "formset_hora": formset_hora,
            "formset_parada": formset_parada,
            "titulo": "Novo Registro de Produção",
        })

    # GET
    form = RegistroProducaoForm()
    formset_hora = RegistroHoraFormSet(prefix="hora")
    formset_parada = ParadaFormSet(prefix="parada")
    return render(request, "registros/form.html", {
        "form": form,
        "formset_hora": formset_hora,
        "formset_parada": formset_parada,
        "titulo": "Novo Registro de Produção",
    })


@login_required
def editar_registro(request, pk):
    registro = get_object_or_404(RegistroProducao, pk=pk)

    if request.method == "POST":
        post_data = request.POST

        # Adicionar
        if "add_hora" in post_data:
            post_data = _increment_total_forms(post_data, "hora")
        if "add_parada" in post_data:
            post_data = _increment_total_forms(post_data, "parada")

        # Remover
        if "rem_hora" in post_data:
            post_data = _remove_formset_row(post_data, "hora", post_data.get("rem_hora"))
        if "rem_parada" in post_data:
            post_data = _remove_formset_row(post_data, "parada", post_data.get("rem_parada"))

        form = RegistroProducaoForm(post_data, instance=registro)
        formset_hora = RegistroHoraFormSet(post_data, instance=registro, prefix="hora")
        formset_parada = ParadaFormSet(post_data, instance=registro, prefix="parada")

        if "salvar" in request.POST and form.is_valid() and formset_hora.is_valid() and formset_parada.is_valid():
            registro = form.save()

            formset_hora.instance = registro
            formset_hora.save()

            formset_parada.instance = registro
            formset_parada.save()

            registro.quantidade_produzida = sum(h.quantidade_produzida for h in registro.registros_hora.all())
            registro.quantidade_defeituosa = sum(h.quantidade_defeituosa for h in registro.registros_hora.all())
            registro.save(update_fields=["quantidade_produzida", "quantidade_defeituosa"])

            messages.success(request, "Registro atualizado com sucesso.")
            return redirect("registros-detalhes", pk=registro.pk)

        return render(request, "registros/form.html", {
            "form": form,
            "formset_hora": formset_hora,
            "formset_parada": formset_parada,
            "titulo": f"Editar Registro {registro.pk}",
        })

    # GET
    form = RegistroProducaoForm(instance=registro)
    formset_hora = RegistroHoraFormSet(instance=registro, prefix="hora")
    formset_parada = ParadaFormSet(instance=registro, prefix="parada")
    return render(request, "registros/form.html", {
        "form": form,
        "formset_hora": formset_hora,
        "formset_parada": formset_parada,
        "titulo": f"Editar Registro {registro.pk}",
    })


# =========================
# CRUD de usuários (somente superuser)
# =========================

def _so_superuser(u):
    return u.is_authenticated and u.is_superuser


@login_required
@user_passes_test(_so_superuser)
def lista_usuarios(request):
    qs = User.objects.order_by("username")
    q = request.GET.get("q")
    if q:
        qs = qs.filter(username__icontains=q)
    paginator = Paginator(qs, 10)
    page = request.GET.get("page")
    usuarios = paginator.get_page(page)
    return render(request, "usuarios/lista.html", {"usuarios": usuarios, "q": q or ""})


@login_required
@user_passes_test(_so_superuser)
def criar_usuario(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuário criado com sucesso.")
            return redirect("lista_usuarios")
    else:
        form = CustomUserCreationForm()
    return render(request, "usuarios/form.html", {"form": form, "titulo": "Criar usuário"})


@login_required
@user_passes_test(_so_superuser)
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuário atualizado com sucesso.")
            return redirect("lista_usuarios")
    else:
        form = CustomUserChangeForm(instance=usuario)
    return render(request, "usuarios/form.html", {"form": form, "titulo": f"Editar usuário: {usuario.username}"})


@login_required
@user_passes_test(_so_superuser)
def deletar_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        if request.user == usuario:
            messages.error(request, "Você não pode deletar a si mesmo.")
            return redirect("lista_usuarios")
        usuario.delete()
        messages.success(request, "Usuário deletado com sucesso.")
        return redirect("lista_usuarios")
    return render(request, "usuarios/confirmar_delete.html", {"usuario": usuario})
# === Ações: Finalizar / Reabrir Registro ===
@login_required
def registro_finalizar(request, pk):
    registro = get_object_or_404(RegistroProducao, pk=pk)
    if not registro.finalizada:
        registro.finalizar()
        messages.success(request, "Registro finalizado com sucesso.")
    return redirect("registros-lista")

@login_required
def registro_reabrir(request, pk):
    registro = get_object_or_404(RegistroProducao, pk=pk)
    if registro.finalizada:
        registro.reabrir()
        messages.success(request, "Registro reaberto com sucesso.")
    return redirect("registros-lista")
