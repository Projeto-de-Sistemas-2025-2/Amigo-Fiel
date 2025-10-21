from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('iniciar/<int:pet_id>/', views.iniciar_chat_com_dono, name='iniciar-chat-com-dono'),
    path('<str:username>/', views.thread_by_username, name='thread'),
    path('api/<str:username>/since/', views.api_thread_since, name='api-thread-since'),
]
