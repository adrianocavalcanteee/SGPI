from django.urls import path
from sgpi import views

urlpatterns = [
    
    path("linhas/", views.LinhaProducaoListView.as_view(), name="linhas-lista"),
    path("linhas/<int:pk>/", views.LinhaProducaoDetailView.as_view(), name="linhas-detalhes"),
    path("linhas/criar/", views.LinhaProducaoCreateView.as_view(), name="linhas-criar"),
    path("linhas/<int:pk>/editar/", views.LinhaProducaoUpdateView.as_view(), name="linhas-editar"),
    path("linhas/<int:pk>/deletar/", views.LinhaProducaoDeleteView.as_view(), name="linhas-deletar"),

    
    path("registros/", views.RegistroProducaoListView.as_view(), name="registros-lista"),
    path("registros/<int:pk>/", views.RegistroProducaoDetailView.as_view(), name="registros-detalhes"),
]
