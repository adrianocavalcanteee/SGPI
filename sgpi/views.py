# app/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from .forms import PermissaoSetorUsuarioFormSet

from .models import LinhaProducao, RegistroProducao, PermissaoSetorUsuario
from .forms import (
    RegistroProducaoForm,
    RegistroHoraFormSet,
    ParadaFormSet,
    CustomUserCreationForm,
    CustomUserChangeForm,
)

# =========================
# Helpers/perfis
# =========================

def _so_superuser(u):
    return u.is_authenticated and u.is_superuser


# =========================
# Helpers para formsets (sem JS)
# =========================

def _increment_total_forms(post_data, prefix: str):
    data = post_data.copy()
    key = f"{prefix}-TOTAL_FORMS"
    data[key] = str(int(data.get(key, "0")) + 1)
    return data


def _remove_formset_row(post_data, prefix: str, pressed_value: str):
    data = post_data.copy()  
    try:
        idx = int(pressed_value.split("-")[1])
    except Exception:
        return data

    total = int(data.get(f"{prefix}-TOTAL_FORMS", "0"))
    initial = int(data.get(f"{prefix}-INITIAL_FORMS", "0"))

    if idx >= total:
        return data 

    if idx < initial:
       
        data.setlist(f"{prefix}-{idx}-DELETE", ["on"])
        return data

   
    for i in range(idx + 1, total):
        old_prefix = f"{prefix}-{i}-"
        new_prefix = f"{prefix}-{i-1}-"

        keys_i = [k for k in data.keys() if k.startswith(old_prefix)]
        for key in keys_i:
            vals = data.getlist(key)
            new_key = key.replace(old_prefix, new_prefix, 1)
            data.setlist(new_key, vals)
            try:
                del data[key]
            except KeyError:
                pass

    
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

       
        user = self.request.user
        if user.is_authenticated and not user.is_superuser:
            setores = list(
                PermissaoSetorUsuario.objects
                .filter(usuario=user)
                .values_list("setor", flat=True)
            )
            
            qs = qs.filter(linha__setor__in=setores) if setores else qs.none()

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

        total_produzido = sum((h.quantidade_produzida or 0) for h in producao_hora)
        total_defeituoso = sum((h.quantidade_defeituosa or 0) for h in producao_hora)
        tempo_parado_total = sum((p.duracao or 0) for p in paradas)  # minutos
        motivos_paradas = [p.motivo for p in paradas if (p.motivo or "").strip()]

        context.update({
            "producao_hora": producao_hora,
            "paradas": paradas,
            "total_produzido": total_produzido,
            "total_defeituoso": total_defeituoso,
            "tempo_parado_total": tempo_parado_total,
            "motivos_paradas": motivos_paradas,
        })
        return context


@login_required
def criar_registro(request):
    if request.method == "POST":
        post_data = request.POST

        # add/rem sem JS
        if "add_hora" in post_data:
            post_data = _increment_total_forms(post_data, "hora")
        if "add_parada" in post_data:
            post_data = _increment_total_forms(post_data, "parada")
        if "rem_hora" in post_data:
            post_data = _remove_formset_row(post_data, "hora", post_data.get("rem_hora"))
        if "rem_parada" in post_data:
            post_data = _remove_formset_row(post_data, "parada", post_data.get("rem_parada"))

        # salvar
        if "salvar" in post_data:
            form = RegistroProducaoForm(post_data, user=request.user)
            if form.is_valid():
                registro = form.save()

                formset_hora = RegistroHoraFormSet(post_data, instance=registro, prefix="hora")
                formset_parada = ParadaFormSet(post_data, instance=registro, prefix="parada")

                if formset_hora.is_valid() and formset_parada.is_valid():
                    formset_hora.save()
                    formset_parada.save()

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

            formset_hora = RegistroHoraFormSet(post_data, prefix="hora")
            formset_parada = ParadaFormSet(post_data, prefix="parada")
            return render(request, "registros/form.html", {
                "form": form,
                "formset_hora": formset_hora,
                "formset_parada": formset_parada,
                "titulo": "Novo Registro de Produção",
            })

        # só add/rem → re-renderiza
        form = RegistroProducaoForm(post_data, user=request.user)
        formset_hora = RegistroHoraFormSet(post_data, prefix="hora")
        formset_parada = ParadaFormSet(post_data, prefix="parada")
        return render(request, "registros/form.html", {
            "form": form,
            "formset_hora": formset_hora,
            "formset_parada": formset_parada,
            "titulo": "Novo Registro de Produção",
        })

    # GET
    form = RegistroProducaoForm(user=request.user)
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

        # add/rem sem JS
        if "add_hora" in post_data:
            post_data = _increment_total_forms(post_data, "hora")
        if "add_parada" in post_data:
            post_data = _increment_total_forms(post_data, "parada")
        if "rem_hora" in post_data:
            post_data = _remove_formset_row(post_data, "hora", post_data.get("rem_hora"))
        if "rem_parada" in post_data:
            post_data = _remove_formset_row(post_data, "parada", post_data.get("rem_parada"))

        # salvar
        if "salvar" in post_data:
            form = RegistroProducaoForm(post_data, instance=registro, user=request.user)
            if form.is_valid():
                registro = form.save()

                formset_hora = RegistroHoraFormSet(post_data, instance=registro, prefix="hora")
                formset_parada = ParadaFormSet(post_data, instance=registro, prefix="parada")

                if formset_hora.is_valid() and formset_parada.is_valid():
                    formset_hora.save()
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

            formset_hora = RegistroHoraFormSet(post_data, instance=registro, prefix="hora")
            formset_parada = ParadaFormSet(post_data, instance=registro, prefix="parada")
            return render(request, "registros/form.html", {
                "form": form,
                "formset_hora": formset_hora,
                "formset_parada": formset_parada,
                "titulo": f"Editar Registro {registro.pk}",
            })

        # só add/rem → re-renderiza
        form = RegistroProducaoForm(post_data, instance=registro, user=request.user)
        formset_hora = RegistroHoraFormSet(post_data, instance=registro, prefix="hora")
        formset_parada = ParadaFormSet(post_data, instance=registro, prefix="parada")
        return render(request, "registros/form.html", {
            "form": form,
            "formset_hora": formset_hora,
            "formset_parada": formset_parada,
            "titulo": f"Editar Registro {registro.pk}",
        })

    # GET inicial
    form = RegistroProducaoForm(instance=registro, user=request.user)
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

@login_required
@user_passes_test(_so_superuser)
def criar_usuario(request):
    from .forms import PermissaoSetorUsuarioFormSet 

    if request.method == "POST":
        post_data = request.POST.copy()

        is_addrem = False
        if "add_perm" in post_data:
            post_data = _increment_total_forms(post_data, "perm")
            is_addrem = True
        if "rem_perm" in post_data:
            post_data = _remove_formset_row(post_data, "perm", post_data.get("rem_perm"))
            is_addrem = True

        
        if is_addrem:
            form = CustomUserCreationForm(post_data)
            dummy = User()  
            perm_formset = PermissaoSetorUsuarioFormSet(post_data, instance=dummy, prefix="perm")
            return render(request, "usuarios/form.html", {
                "form": form,
                "perm_formset": perm_formset,
                "titulo": "Criar usuário",
            })

       
        form = CustomUserCreationForm(post_data)
        if form.is_valid():
            usuario = form.save()
            perm_formset = PermissaoSetorUsuarioFormSet(post_data, instance=usuario, prefix="perm")
            if perm_formset.is_valid():
                perm_formset.save()
                messages.success(request, "Usuário criado com sucesso.")
                return redirect("lista_usuarios")

            
            return render(request, "usuarios/form.html", {
                "form": CustomUserChangeForm(instance=usuario),
                "perm_formset": perm_formset,
                "titulo": f"Editar usuário: {usuario.username}",
            })

        
        dummy = User()
        perm_formset = PermissaoSetorUsuarioFormSet(post_data, instance=dummy, prefix="perm")
        return render(request, "usuarios/form.html", {
            "form": form,
            "perm_formset": perm_formset,
            "titulo": "Criar usuário",
        })

    
    form = CustomUserCreationForm()
    dummy = User()
    from .forms import PermissaoSetorUsuarioFormSet
    perm_formset = PermissaoSetorUsuarioFormSet(instance=dummy, prefix="perm")
    return render(request, "usuarios/form.html", {
        "form": form,
        "perm_formset": perm_formset,
        "titulo": "Criar usuário",
    })

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
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    from .forms import PermissaoSetorUsuarioFormSet

    if request.method == "POST":
        post_data = request.POST

        if "add_perm" in post_data:
            post_data = _increment_total_forms(post_data, "perm")
        if "rem_perm" in post_data:
            post_data = _remove_formset_row(post_data, "perm", post_data.get("rem_perm"))

        if "salvar" in post_data:
            form = CustomUserChangeForm(post_data, instance=usuario)
            perm_formset = PermissaoSetorUsuarioFormSet(post_data, instance=usuario, prefix="perm")
            if form.is_valid() and perm_formset.is_valid():
                form.save()
                perm_formset.save()
                messages.success(request, "Usuário atualizado com sucesso.")
                return redirect("lista_usuarios")

            return render(request, "usuarios/form.html", {
                "form": form,
                "perm_formset": perm_formset,
                "titulo": f"Editar usuário: {usuario.username}",
            })

        form = CustomUserChangeForm(post_data, instance=usuario)
        perm_formset = PermissaoSetorUsuarioFormSet(post_data, instance=usuario, prefix="perm")
        return render(request, "usuarios/form.html", {
            "form": form,
            "perm_formset": perm_formset,
            "titulo": f"Editar usuário: {usuario.username}",
        })

    form = CustomUserChangeForm(instance=usuario)
    perm_formset = PermissaoSetorUsuarioFormSet(instance=usuario, prefix="perm")
    return render(request, "usuarios/form.html", {
        "form": form,
        "perm_formset": perm_formset,
        "titulo": f"Editar usuário: {usuario.username}",
    })



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

#Redefinir senha
def forgot_password(request):
    return render(request, "registration/forgot_password.html")