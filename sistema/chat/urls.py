from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<str:username>/', views.thread_by_username, name='thread'),
    path('api/<str:username>/since/', views.api_thread_since, name='api-thread-since'),
]
