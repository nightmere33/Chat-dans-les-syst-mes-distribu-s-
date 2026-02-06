import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Set the default Django settings module for the 'asgi' application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')

# Initialize Django FIRST
django.setup()

# Now import Django's ASGI application and your routing
from django.core.asgi import get_asgi_application
import chat.routing

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})