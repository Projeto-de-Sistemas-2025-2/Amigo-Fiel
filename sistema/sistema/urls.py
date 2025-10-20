from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from AmigoFiel import views as amigofiel_views
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', RedirectView.as_view(url='/amigofiel/', permanent=False)),

    path('admin/', admin.site.urls),

    # Auth
    path('login/',  auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', amigofiel_views.LogoutView.as_view(), name='logout'),

    # Cadastro
    path('cadastro/', amigofiel_views.cadastro, name='cadastro'),

    # App principal (uma vez só!)
    path('amigofiel/', include(('AmigoFiel.urls', 'amigofiel'), namespace='amigofiel')),
    path('AmigoFiel/', RedirectView.as_view(url='/amigofiel/', permanent=False)),


    # Chat
    path('chat/', include(('chat.urls', 'chat'), namespace='chat')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
