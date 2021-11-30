from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Group(models.Model):
    name = models.CharField(max_length=30)

    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='guilds')
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self) -> str:
        return f'{self.name}'


class GroupMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='group_membership')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_members')

    admin = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    banned = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.group}: {self.user}'


class GroupMessage(models.Model):
    author = models.ForeignKey(GroupMember, on_delete=models.CASCADE, related_name='groupmember_messages')
    text = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.author}: {self.text}'
