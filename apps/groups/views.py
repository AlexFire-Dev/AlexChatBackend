from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .models import *
from . import serializers


class GroupViewSet(viewsets.ViewSet):
    """ ViewSet групп """

    permission_classes = [permissions.IsAuthenticated]

    group_response = openapi.Response('', serializers.GetUpdateGroupSerializer)
    groups_response = openapi.Response('', serializers.GetUpdateGroupSerializer(many=True))

    @swagger_auto_schema(responses={'200': group_response})
    def retrieve(self, request, pk=None) -> Response:
        instance = self.get_object(pk)
        serializer = serializers.GetUpdateGroupSerializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(responses={'200': group_response})
    def list(self, request) -> Response:
        queryset = Group.objects.filter(group_members__user=request.user)
        serializer = serializers.GetUpdateGroupSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=serializers.CreateGroupSerializer)
    def create(self, request) -> Response:
        serializer = serializers.CreateGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save(creator=request.user)
        GroupMember.objects.create(user=request.user, group=group, admin=True)
        GroupInviteLink.objects.create(group=group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=serializers.GetUpdateGroupSerializer)
    def partial_update(self, request, pk=None) -> Response:
        instance = self.get_object(pk)
        if instance.creator != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.GetUpdateGroupSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, pk=None) -> Response:
        instance = self.get_object(pk)
        if instance.creator != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self, pk):
        obj = get_object_or_404(Group, id=pk)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class GroupMemberViewSet(viewsets.ViewSet):
    """ ViewSet участников группы """

    permission_classes = [permissions.IsAuthenticated]

    membership_response = openapi.Response('', serializers.GroupMemberSerializer)
    memberships_response = openapi.Response('', serializers.GroupMemberSerializer(many=True))

    @swagger_auto_schema(responses={'200': memberships_response})
    def list(self, request) -> Response:
        queryset = GroupMember.objects.filter(user=request.user)
        serializer = serializers.GroupMemberSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(responses={'200': membership_response})
    def retrieve(self, request, pk=None) -> Response:
        instance = self.get_object(pk)
        serializer = serializers.GroupMemberSerializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=serializers.GroupInviteLinkSerializer, responses={'201': membership_response})
    def create(self, request) -> Response:
        serializer = serializers.GroupInviteLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data['key']
        link = get_object_or_404(GroupInviteLink, key=key)
        member, _ = GroupMember.objects.get_or_create(user=request.user, group=link.group)
        if not member.banned:
            member.active = True
            member.save()
        return Response(serializers.GroupMemberSerializer(member).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None) -> Response:
        instance = self.get_object(pk)
        if instance.user != instance.group.creator:
            instance.admin = False
            instance.active = False
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

    def get_object(self, pk):
        obj = get_object_or_404(GroupMember, id=pk, user=self.request.user)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class GroupInviteLinkViewSet(viewsets.ViewSet):
    """ ViewSet кода приглашения """

    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, pk=None):
        group = get_object_or_404(Group, id=pk)
        member = get_object_or_404(GroupMember, group=group, user=self.request.user, admin=True)
        obj = get_object_or_404(GroupInviteLink, group=group)
        serializer = serializers.GroupInviteLinkSerializer(obj)
        return Response(serializer.data)


class GroupMessageViewSet(viewsets.ViewSet):
    """ ViewSet сообщений группы """

    permission_classes = [permissions.IsAuthenticated]

    messages_response = openapi.Response('', serializers.GroupMessageSerializer(many=True))

    @swagger_auto_schema(responses={'200': messages_response})
    def list(self, request, pk=None) -> Response:
        group = get_object_or_404(Group, id=pk)
        member = get_object_or_404(GroupMember, group=group, user=self.request.user)
        queryset = GroupMessage.objects.filter(author__group=group).order_by('-id')

        paginator = Paginator(queryset, 15)
        page = request.GET.get('page')

        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = serializers.GroupMessageSerializer(queryset, many=True)
        return Response(serializer.data)
