from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from .models import ChatRoom, Message
from accounts.models import CustomUser


@login_required
def lobby_view(request):
    rooms = ChatRoom.objects.filter(is_private=False)
    
    # Utilisateurs actifs dans les 5 dernières minutes
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    online_users = CustomUser.objects.filter(
        last_seen__gte=five_minutes_ago
    ).exclude(id=request.user.id)
    
    # Marquer comme en ligne pour la compatibilité
    for user in online_users:
        user.is_online = True
    
    return render(request, 'chat/lobby.html', {
        'rooms': rooms,
        'online_users': online_users,
    })

@login_required
def room_view(request, room_name):
    # Nettoyer le nom de la salle
    room_name = room_name.strip()
    
    # Récupérer la salle ou 404
    room = get_object_or_404(ChatRoom, name=room_name)
    
    # Récupérer les 50 derniers messages POUR LES AFFICHER DIRECTEMENT
    messages = Message.objects.filter(room=room).select_related('user').order_by('timestamp')[:50]
    
    # Préparer les messages pour le template
    message_list = []
    for msg in messages:
        message_list.append({
            'id': msg.id,
            'content': msg.content,
            'username': msg.user.username,
            'avatar': msg.user.avatar.url if msg.user.avatar else '/media/avatars/default.png',
            'timestamp': msg.timestamp.isoformat(),
            'is_current_user': msg.user == request.user,
        })
    
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'room': room,
        'initial_messages': message_list,  # Ajout des messages initiaux
    })

@login_required
def create_room_view(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validation
        if not room_name:
            messages.error(request, 'Le nom de la salle est requis.')
            return redirect('chat:lobby')
        
        if len(room_name) > 100:
            messages.error(request, 'Le nom de la salle ne peut pas dépasser 100 caractères.')
            return redirect('chat:lobby')
        
        # Normaliser le nom
        normalized_name = room_name.lower().replace(' ', '_')
        # Nettoyer les caractères spéciaux
        normalized_name = ''.join(c for c in normalized_name if c.isalnum() or c == '_')
        
        # Vérifier si la salle existe déjà
        if ChatRoom.objects.filter(name=normalized_name).exists():
            messages.error(request, f'Une salle nommée "{room_name}" existe déjà.')
            return redirect('chat:lobby')
        
        # Créer la salle
        try:
            room = ChatRoom.objects.create(
                name=normalized_name,
                description=description,
                creator=request.user
            )
            messages.success(request, f'Salle "{room_name}" créée avec succès!')
            return redirect('chat:room', room_name=normalized_name)
            
        except Exception as e:
            messages.error(request, f'Erreur technique: {str(e)}')
            return redirect('chat:lobby')
    
    # Si ce n'est pas un POST, rediriger vers le lobby
    return redirect('chat:lobby')

@login_required
def delete_room_view(request, room_name):
    try:
        room = ChatRoom.objects.get(name=room_name)
        
        # Vérifier les permissions
        if room.creator != request.user and not request.user.is_superuser:
            messages.error(request, 'Vous ne pouvez supprimer que les salles que vous avez créées.')
            return redirect('chat:lobby')
        
        # Supprimer
        room_name_display = room.name
        room.delete()
        messages.success(request, f'Salle "{room_name_display}" supprimée avec succès.')
        
    except ChatRoom.DoesNotExist:
        messages.error(request, 'Cette salle n\'existe pas.')
    
    return redirect('chat:lobby')