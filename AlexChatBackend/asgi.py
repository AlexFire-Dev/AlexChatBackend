"""
ASGI config for AlexChatBackend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AlexChatBackend.settings')

application = get_asgi_application()
django.setup()
django_asgi_app = get_asgi_application()


import apps.ws_routes
from apps.base.middleware import TokenAuthMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': TokenAuthMiddleware(
        URLRouter(
            apps.ws_routes.websocket_urlpatterns
        )
    ),
})
