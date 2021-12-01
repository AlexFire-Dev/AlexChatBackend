from rest_framework import serializers

from . import models


class CreateGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        fields = ('id', 'name')


class GetUpdateGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        fields = ('id', 'name', 'creator', 'created')


class GroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GroupMember
        fields = ('id', 'user', 'group', 'admin', 'active', 'banned')


class GroupInviteLinkSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=40, required=True)
