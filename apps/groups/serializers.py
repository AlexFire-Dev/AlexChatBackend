from django.contrib.auth import get_user_model
from rest_framework import serializers

from . import models


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username')


class CreateGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        fields = ('id', 'name')


class GetUpdateGroupSerializer(serializers.ModelSerializer):
    creator = UserSerializer()

    class Meta:
        model = models.Group
        fields = ('id', 'name', 'creator', 'created')


class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = models.GroupMember
        fields = ('id', 'user', 'group', 'admin', 'active', 'banned')


class GroupMessageSerializer(serializers.ModelSerializer):
    author = GroupMemberSerializer()

    class Meta:
        model = models.GroupMessage
        fields = ('id', 'author', 'text', 'created', 'updated')


class GroupInviteLinkSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=40, required=True)
