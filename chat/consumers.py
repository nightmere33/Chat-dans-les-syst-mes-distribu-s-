import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatRoom, Message, CustomUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Vérifier si l'utilisateur est authentifié
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Récupérer les 50 derniers messages
        messages = await self.get_last_messages()
        for message in messages:
            await self.send(text_data=json.dumps({
                'type': 'old_message',
                'message': message['content'],
                'username': message['username'],
                'avatar': message['avatar'],
                'timestamp': message['timestamp']
            }))
        
        # Notifier que l'utilisateur a rejoint
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': self.scope['user'].username,
            }
        )

    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notifier que l'utilisateur a quitté
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'username': self.scope['user'].username,
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = self.scope['user'].username
        avatar = self.scope['user'].avatar.url if self.scope['user'].avatar else '/media/avatars/default.png'
        
        # Sauvegarder le message dans la base de données
        await self.save_message(message)
        
        # Envoyer le message à tous les membres du groupe
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'avatar': avatar,
            }
        )

    async def chat_message(self, event):
        # Envoyer le message au WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'avatar': event['avatar'],
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': event['username'],
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'username': event['username'],
        }))

    @database_sync_to_async
    def save_message(self, content):
        room = ChatRoom.objects.get(name=self.room_name)
        Message.objects.create(
            room=room,
            user=self.scope['user'],
            content=content
        )

    @database_sync_to_async
    def get_last_messages(self):
        room = ChatRoom.objects.get(name=self.room_name)
        messages = Message.objects.filter(room=room).select_related('user').order_by('-timestamp')[:50]
        
        return [
            {
                'content': msg.content,
                'username': msg.user.username,
                'avatar': msg.user.avatar.url if msg.user.avatar else '/media/avatars/default.png',
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in reversed(messages)
        ]