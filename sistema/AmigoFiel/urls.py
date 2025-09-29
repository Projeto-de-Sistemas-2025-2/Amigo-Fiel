# AmigoFiel/urls.py
from django.urls import path
from .views import HomeView, ListarAnimais, cadastro, ListarOngs, SobreView, ContatoView, ListarLojas
from . import views

app_name = "amigofiel"

urlpatterns = [

    path("cadastro/", cadastro, name="cadastro"),

    # Home
    path("", HomeView.as_view(), name="home"),
    path("adotar/", ListarAnimais.as_view(), name="listar-animais"),
    path("ongs/", ListarOngs.as_view(), name="listar-ongs"),
    path("animais/", ListarAnimais.as_view(), name="listar-animais"),

    # Lojas e produtos
    path("lojas/",  ListarLojas.as_view(),  name="listar-lojas"),
    path("produtos/", views.ListarProdutos.as_view(), name="listar-produtos"),

    # Lojas e produtos
    path("sobre/", SobreView.as_view(), name="sobre"),
    path("contato/", ContatoView.as_view(), name="contato"),

    # Perfis
    path("@<str:handle>/", views.perfil_usuario, name="perfil-usuario"),
    path("Co./<str:handle>/", views.perfil_empresa, name="perfil-empresa"),
    path("ONG/<str:handle>/", views.perfil_ong,     name="perfil-ong"),
    path("pet/<slug:handle>/", views.perfil_pet,     name="perfil-pet"),

    # Produto: /amigofiel/<empresa_handle>/<produto_slug>/
    path("<str:empresa_handle>/<slug:produto_slug>/", views.produto_detalhe, name="produto-detalhe"),

]
