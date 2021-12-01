from django.urls import re_path, path

from .groups.consumers import *


websocket_urlpatterns = [
    path('ws/groups/<int:pk>/', GroupConsumer.as_asgi())
]
