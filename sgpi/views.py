# app/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import LinhaProducao, RegistroProducao
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from .forms import RegistroProducaoForm, RegistroHoraFormSet

from .forms import CustomUserCreationForm, CustomUserChangeForm


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

class RegistroProducaoListView(ListView):
    model = RegistroProducao
    template_name = "registros/lista.html"
    context_object_name = "registros"
    ordering = ["-data", "turno"]


class RegistroProducaoDetailView(DetailView):
    model = RegistroProducao
    template_name = "registros/detalhes.html"
    context_object_name = "registro"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registro = self.object
        # Produção hora a hora
        context['producao_hora'] = registro.registros_hora.all()
        # Paradas do registro
        context['paradas'] = registro.paradas.all()
        return context


@login_required
def criar_registro(request):
    if request.method == "POST":
        form = RegistroProducaoForm(request.POST)
        formset = RegistroHoraFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            
            registro = form.save(commit=False)
            registro.save()

            
            formset.instance = registro
            formset.save()

          
            total_produzido = sum(h.quantidade_produzida for h in registro.registros_hora.all())
            registro.quantidade_produzida = total_produzido
            registro.save(update_fields=['quantidade_produzida'])

            messages.success(request, "Registro criado com sucesso.")
            return redirect("registros-lista")
    else:
        form = RegistroProducaoForm()
        formset = RegistroHoraFormSet()

    return render(request, "registros/form.html", {
        "form": form,
        "formset": formset,
        "titulo": "Novo Registro de Produção"
    })

@login_required
def editar_registro(request, pk):
    registro = get_object_or_404(RegistroProducao, pk=pk)

    if request.method == "POST":
        form = RegistroProducaoForm(request.POST, instance=registro)
        formset = RegistroHoraFormSet(request.POST, instance=registro)

        if form.is_valid() and formset.is_valid():
          
            form.save()
           
            formset.save()

            
            total_produzido = sum(h.quantidade_produzida for h in registro.registros_hora.all())
            registro.quantidade_produzida = total_produzido
            registro.save(update_fields=['quantidade_produzida'])

            messages.success(request, "Registro atualizado com sucesso.")
            return redirect("registros-lista")

    else:
        form = RegistroProducaoForm(instance=registro)
        formset = RegistroHoraFormSet(instance=registro)

    return render(request, "registros/form.html", {
        "form": form,
        "formset": formset,
        "titulo": f"Editar Registro {registro.pk}"
    })


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

#views do CRUD de users
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
