from django.urls import path, include

from .views import *


urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),

    path('notifications/', NotificationTokenViewSet.as_view({'post': 'update'})),
]
