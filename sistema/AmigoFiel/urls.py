from django.urls import path
from .views import HomeView, ListarAnimais

app_name = "amigofiel"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("animais/", ListarAnimais.as_view(), name="listar-animais"),
]
