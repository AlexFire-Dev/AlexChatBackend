from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .models import *
from . import serializers


class NotificationTokenViewSet(viewsets.ViewSet):
    """ ViewSet для NotificationToken """

    permission_classes = [permissions.IsAuthenticated]

    def update(self, request):
        instance, _ = NotificationToken.objects.get_or_create(user=self.request.user)
        serializer = serializers.NotificationTokenSerializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
