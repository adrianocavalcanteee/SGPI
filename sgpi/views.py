# app/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import LinhaProducao, RegistroProducao
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CustomUserCreationForm, CustomUserChangeForm


class LinhaProducaoListView(ListView):
    model = LinhaProducao
    template_name = "linhas/lista.html"
    context_object_name = "linhas"


class LinhaProducaoDetailView(DetailView):
    model = LinhaProducao
    template_name = "linhas/detalhes.html"
    context_object_name = "linha"


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


class RegistroProducaoDetailView(DetailView):
    model = RegistroProducao
    template_name = "registros/detalhes.html"
    context_object_name = "registro"


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
