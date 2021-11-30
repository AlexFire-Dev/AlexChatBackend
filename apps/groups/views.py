from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .models import *
from . import serializers


class GroupViewSet(viewsets.ViewSet):
    """ ViewSet групп """

    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, pk=None) -> Response:
        instance = self.get_object(pk)
        serializer = serializers.GetUpdateGroupSerializer(instance)
        return Response(serializer.data)

    def list(self, request) -> Response:
        queryset = Group.objects.filter(group_members__user=request.user)
        serializer = serializers.GetUpdateGroupSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=serializers.CreateGroupSerializer)
    def create(self, request) -> Response:
        serializer = serializers.CreateGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(creator=request.user)
        group = serializer.save()
        GroupMember.objects.create(user=request.user, group=group, admin=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=serializers.GetUpdateGroupSerializer)
    def partial_update(self, request, pk=None) -> Response:
        instance = self.get_object(pk)
        serializer = serializers.GetUpdateGroupSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get_object(self, pk):
        obj = get_object_or_404(Group, id=pk)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
