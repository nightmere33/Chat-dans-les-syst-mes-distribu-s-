# accounts/middleware.py
from django.utils import timezone

class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Mettre à jour last_seen pour les utilisateurs authentifiés
        if request.user.is_authenticated:
            user = request.user
            user.last_seen = timezone.now()
            user.save(update_fields=['last_seen'])
        
        return response