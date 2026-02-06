#!/usr/bin/env python
"""
Setup script for Render deployment
"""
import os
import sys
import django

# Add the project to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')

# Initialize Django
django.setup()

from django.contrib.auth import get_user_model
from chat.models import ChatRoom

def setup_default_data():
    """Create default chat rooms and admin user if needed"""
    User = get_user_model()
    
    # Create admin user if it doesn't exist
    if not User.objects.filter(username='admin').exists():
        print("Creating admin user...")
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'  # Change this in production!
        )
        print("Admin user created: username=admin, password=admin123")
    
    # Create default chat rooms
    default_rooms = [
        ('general', 'General discussion room'),
        ('random', 'Random topics and fun'),
        ('help', 'Help and support'),
        ('projects', 'Project discussions'),
    ]
    
    for room_name, description in default_rooms:
        if not ChatRoom.objects.filter(name=room_name).exists():
            ChatRoom.objects.create(
                name=room_name,
                description=description
            )
            print(f"Created room: {room_name}")

if __name__ == '__main__':
    setup_default_data()