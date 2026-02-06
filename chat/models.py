# chat/models.py
from django.db import models
from accounts.models import CustomUser

class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)
    creator = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_rooms'
    )
    
    def __str__(self):
        return self.name
    
    def display_name(self):
        # Méthode pour afficher le nom joliment
        if hasattr(self, '_display_name'):
            return self._display_name
        # Remplacer les underscores par des espaces
        return self.name.replace('_', ' ').title()
    
    def get_message_count(self):
        return self.messages.count()
    
    class Meta:
        ordering = ['-created_at']

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    seen_by = models.ManyToManyField(
        CustomUser, 
        related_name='seen_messages',
        blank=True
    )
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'
    
    def is_seen_by(self, user):
        return self.seen_by.filter(id=user.id).exists()