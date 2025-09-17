# sgpi/urls.py
from django.urls import path
from sgpi import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ----------------------------
    # Linhas de produção
    # ----------------------------
    path("linhas/", views.LinhaProducaoListView.as_view(), name="linhas-lista"),
    path("linhas/criar/", views.LinhaProducaoCreateView.as_view(), name="linhas-criar"),
    path("linhas/<int:pk>/editar/", views.LinhaProducaoUpdateView.as_view(), name="linhas-editar"),
    path("linhas/<int:pk>/deletar/", views.LinhaProducaoDeleteView.as_view(), name="linhas-deletar"),

    # URLs para registros
    path("registros/", views.RegistroProducaoListView.as_view(), name="registros-lista"),
    path("registros/<int:pk>/", views.RegistroProducaoDetailView.as_view(), name="registros-detalhes"),
    path("registros/criar/", views.RegistroProducaoCreateView.as_view(), name="registros-criar"),
    path("registros/<int:pk>/editar/", views.RegistroProducaoUpdateView.as_view(), name="registros-editar"),
    # finalizar/reabrir
    path("registros/<int:pk>/finalizar/", views.registro_finalizar, name="registros-finalizar"),
    path("registros/<int:pk>/reabrir/", views.registro_reabrir, name="registros-reabrir"),


    # ----------------------------
    # Auth (login/logout)
    # ----------------------------
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # ----------------------------
    # CRUD de usuários (somente superuser)
    # ----------------------------
    path("usuarios/", views.lista_usuarios, name="lista_usuarios"),
    path("usuarios/criar/", views.criar_usuario, name="criar_usuario"),
    path("usuarios/<int:user_id>/editar/", views.editar_usuario, name="editar_usuario"),
    path("usuarios/<int:user_id>/deletar/", views.deletar_usuario, name="deletar_usuario"),
]
