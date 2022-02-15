from django.urls import re_path, path

from .groups.consumers import *


websocket_urlpatterns = [
    path('groups/connect/', GroupConsumer.as_asgi())
]
