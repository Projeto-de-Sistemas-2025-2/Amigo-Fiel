from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from AmigoFiel import views as amigofiel_views
from django.contrib.auth.views import LogoutView
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('login/',  auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Chat (colocado antes do app principal para evitar que a rota genérica de produto capture /chat/...)
    path('chat/', include(('chat.urls', 'chat'), namespace='chat')),

    # App principal montado na raiz (removendo '/amigofiel/' duplicado na URL)
    path('', include(('AmigoFiel.urls', 'amigofiel'), namespace='amigofiel')),
    # rota antiga com case diferente redireciona para raiz
    path('AmigoFiel/', RedirectView.as_view(url='/', permanent=False)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
