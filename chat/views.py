from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import ChatRoom
from accounts.models import CustomUser

@login_required
def lobby_view(request):
    rooms = ChatRoom.objects.filter(is_private=False)
    online_users = CustomUser.objects.filter(is_online=True).exclude(id=request.user.id)
    
    return render(request, 'chat/lobby.html', {
        'rooms': rooms,
        'online_users': online_users,
    })

@login_required
def room_view(request, room_name):
    try:
        room = ChatRoom.objects.get(name=room_name)
    except ChatRoom.DoesNotExist:
        room = ChatRoom.objects.create(name=room_name)
    
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'room': room,
    })

@login_required
def create_room_view(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        description = request.POST.get('description', '')
        
        if room_name:
            room, created = ChatRoom.objects.get_or_create(
                name=room_name,
                defaults={'description': description}
            )
            return redirect('chat:room', room_name=room_name)
    
    return redirect('chat:lobby')