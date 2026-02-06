from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.lobby_view, name='lobby'),
    path('create/', views.create_room_view, name='create_room'),
    path('<str:room_name>/', views.room_view, name='room'),
    
    path('<str:room_name>/delete/', views.delete_room_view, name='delete_room'),
]