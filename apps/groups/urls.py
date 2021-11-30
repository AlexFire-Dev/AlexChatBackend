from django.urls import path, include

from .views import *


urlpatterns = [
    path('', GroupViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:pk>/', GroupViewSet.as_view({'get': 'retrieve', 'put': 'partial_update'})),
]
