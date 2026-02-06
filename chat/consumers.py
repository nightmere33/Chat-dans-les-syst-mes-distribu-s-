import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from datetime import timedelta
from .models import ChatRoom, Message, CustomUser

class ChatConsumer(AsyncWebsocketConsumer):
    # Stocker les connexions actives par salle
    active_connections = {}
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']
        
        # Vérifier si l'utilisateur est authentifié
        if self.user == AnonymousUser():
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Ajouter l'utilisateur aux connexions actives
        if self.room_name not in self.active_connections:
            self.active_connections[self.room_name] = {}
        
        self.active_connections[self.room_name][self.user.username] = {
            'channel_name': self.channel_name,
            'avatar': self.user.avatar.url if self.user.avatar else '/media/avatars/default.png',
            'joined_at': timezone.now()
        }
        
        # Récupérer les 50 derniers messages AVEC LES HEURES RÉELLES
        messages = await self.get_last_messages()
        for message in messages:
            await self.send(text_data=json.dumps({
                'type': 'old_message',
                'id': message['id'],
                'message': message['content'],
                'username': message['username'],
                'avatar': message['avatar'],
                'timestamp': message['timestamp'],
            }))
        
        # Envoyer la liste des utilisateurs en ligne dans cette salle
        await self.send_online_users()
        
        # Notifier que l'utilisateur a rejoint
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': self.user.username,
                'avatar': self.user.avatar.url if self.user.avatar else '/media/avatars/default.png',
            }
        )

    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Retirer l'utilisateur des connexions actives
        if self.room_name in self.active_connections:
            if self.user.username in self.active_connections[self.room_name]:
                del self.active_connections[self.room_name][self.user.username]
            
            # Supprimer la salle si vide
            if not self.active_connections[self.room_name]:
                del self.active_connections[self.room_name]
        
        # Envoyer la liste mise à jour
        await self.send_online_users()
        
        # Notifier que l'utilisateur a quitté
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'username': self.user.username,
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data['message']
        username = self.user.username
        avatar = self.user.avatar.url if self.user.avatar else '/media/avatars/default.png'
        
        # Sauvegarder le message dans la base de données
        message = await self.save_message(message_content)
        message_id = message.id
        timestamp = message.timestamp.isoformat()
        
        # COMPTEUR d'utilisateurs dans la salle (pour statut)
        users_in_room = 0
        if self.room_name in self.active_connections:
            users_in_room = len(self.active_connections[self.room_name])
        
        # NE PAS envoyer le message à l'expéditeur ici
        # Le client affichera le message de manière optimiste
        
        # Envoyer le message à TOUS les utilisateurs (y compris l'expéditeur)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message_all',
                'id': message_id,
                'message': message_content,
                'username': username,
                'avatar': avatar,
                'timestamp': timestamp,
                'sender_channel': self.channel_name,
            }
        )
        
        # Mettre à jour le statut après délai
        if users_in_room > 1:
            asyncio.create_task(self.update_message_status_delayed(message_id, username, 1))

    async def update_message_status_delayed(self, message_id, username, delay):
        """Met à jour le statut après un délai"""
        await asyncio.sleep(delay)
        
        # Envoyer la mise à jour du statut à l'expéditeur
        if self.room_name in self.active_connections and username in self.active_connections[self.room_name]:
            sender_channel = self.active_connections[self.room_name][username]['channel_name']
            await self.channel_layer.send(
                sender_channel,
                {
                    'type': 'message_status_update',
                    'message_id': message_id,
                    'status': 'delivered',
                }
            )
        
        # Après 2 secondes supplémentaires, marquer comme 'seen' (simulation Instagram)
        await asyncio.sleep(2)
        if self.room_name in self.active_connections and username in self.active_connections[self.room_name]:
            sender_channel = self.active_connections[self.room_name][username]['channel_name']
            await self.channel_layer.send(
                sender_channel,
                {
                    'type': 'message_status_update',
                    'message_id': message_id,
                    'status': 'seen',
                }
            )
    async def chat_message_all(self, event):
        """Envoie le message à TOUS les utilisateurs"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'id': event['id'],
            'message': event['message'],
            'username': event['username'],
            'avatar': event['avatar'],
            'timestamp': event['timestamp'],
            'is_current_user': event['sender_channel'] == self.channel_name,
        }))

    async def chat_message_others(self, event):
        # Envoyer le message aux autres utilisateurs (sauf l'expéditeur)
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'id': event['id'],
                'message': event['message'],
                'username': event['username'],
                'avatar': event['avatar'],
                'timestamp': event['timestamp'],
            }))

    async def message_status_update(self, event):
        """Met à jour le statut d'un message (sent → delivered → seen)"""
        await self.send(text_data=json.dumps({
            'type': 'message_status_update',
            'message_id': event['message_id'],
            'status': event['status'],
        }))

    async def chat_message(self, event):
        # Cette méthode n'est plus utilisée directement
        pass

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': event['username'],
            'avatar': event['avatar'],
        }))
        await self.send_online_users()

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'username': event['username'],
        }))
        await self.send_online_users()

    async def send_online_users(self):
        """Envoyer la liste des utilisateurs en ligne dans la salle"""
        if self.room_name in self.active_connections:
            online_users = list(self.active_connections[self.room_name].keys())
            users_with_avatars = await self.get_users_with_avatars(online_users)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'online_users_list',
                    'online_users': users_with_avatars,
                }
            )

    async def online_users_list(self, event):
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'online_users': event['online_users'],
        }))

    @database_sync_to_async
    def save_message(self, content):
        room = ChatRoom.objects.get(name=self.room_name)
        message = Message.objects.create(
            room=room,
            user=self.user,
            content=content
        )
        return message

    @database_sync_to_async
    def get_last_messages(self):
        room = ChatRoom.objects.get(name=self.room_name)
        messages = Message.objects.filter(room=room).select_related('user').order_by('-timestamp')[:50]
        
        return [
            {
                'id': msg.id,
                'content': msg.content,
                'username': msg.user.username,
                'avatar': msg.user.avatar.url if msg.user.avatar else '/media/avatars/default.png',
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in reversed(messages)  # Plus ancien en premier
        ]

    @database_sync_to_async
    def get_users_with_avatars(self, usernames):
        users = CustomUser.objects.filter(username__in=usernames)
        return [
            {
                'username': user.username,
                'avatar': user.avatar.url if user.avatar else '/media/avatars/default.png',
                'bio': user.bio[:50] if user.bio else ''
            }
            for user in users
        ]