# app/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import LinhaProducao, RegistroProducao


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
