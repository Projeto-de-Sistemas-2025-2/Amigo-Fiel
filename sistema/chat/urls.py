from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<str:username>/', views.thread_by_username, name='thread-by-username'),
    path('api/<str:username>/', views.api_thread_since, name='api-thread-since'),  # polling (opcional)
]
