#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# Create a superuser if it doesn't exist (optional, for admin access)
# Uncomment and modify if needed:
# echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'password')" | python manage.py shell || true

# Create default chat rooms (optional)
echo "Creating default chat rooms..."
python -c "
from django.contrib.auth import get_user_model
from chat.models import ChatRoom
import os

# Get or create admin user
User = get_user_model()
try:
    admin = User.objects.get(username='admin')
except:
    admin = None

# Create general room if it doesn't exist
if not ChatRoom.objects.filter(name='general').exists():
    ChatRoom.objects.create(
        name='general',
        description='General discussion room',
        creator=admin
    )
    print('Created general room')
else:
    print('General room already exists')

if not ChatRoom.objects.filter(name='random').exists():
    ChatRoom.objects.create(
        name='random',
        description='Random topics',
        creator=admin
    )
    print('Created random room')
else:
    print('Random room already exists')
"