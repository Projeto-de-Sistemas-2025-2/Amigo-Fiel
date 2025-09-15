from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from AmigoFiel import views 
# Se você optar por view função e quiser rota /cadastro/ aqui também:
from AmigoFiel.views import cadastro

urlpatterns = [
    path("", include(("AmigoFiel.urls", "amigofiel"), namespace="amigofiel")),  # Rota raiz direciona para AmigoFiel
    path("admin/", admin.site.urls),

    # Autenticação
    path("login/",  auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # Cadastro direto no sistema/urls
    path("cadastro/", views.cadastro, name="cadastro"),

    path("amigofiel/", include(("AmigoFiel.urls","amigofiel"), namespace="amigofiel")),
    
    # Se realmente quiser expor /cadastro/ também a partir do projeto (opcional, evite duplicidade):
    path("cadastro/", cadastro, name="cadastro"),
]



