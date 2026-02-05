from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.lobby_view, name='lobby'),
    path('<str:room_name>/', views.room_view, name='room'),
    path('create/', views.create_room_view, name='create_room'),
]