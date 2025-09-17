from django.urls import path
from .views import HomeView, ListarAnimais, CadastroView

app_name = "amigofiel"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("adotar/", ListarAnimais.as_view(), name="listar-animais"),
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
]