# AmigoFiel/urls.py
from django.urls import path
from .views import HomeView, ListarAnimais, cadastro, ListarOngs, SobreView, ContatoView

app_name = "amigofiel"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("adotar/", ListarAnimais.as_view(), name="listar-animais"),
    path("cadastro/", cadastro, name="cadastro"),
    path("ongs/", ListarOngs.as_view(), name="listar-ongs"),

    path("sobre/", SobreView.as_view(), name="sobre"),
    path("contato/", ContatoView.as_view(), name="contato"),
]
