import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')

application = get_wsgi_application()

# Apply WhiteNoise for static files in production
try:
    from whitenoise import WhiteNoise
    # Check if we're in production (you can also check DEBUG setting)
    if os.getenv('RENDER') or not os.getenv('DEBUG', 'True').lower() == 'true':
        application = WhiteNoise(application, root='staticfiles')
        # Also serve media files in production if needed
        application.add_files('media', prefix='media/')
except ImportError:
    # WhiteNoise not installed, continue without it
    pass