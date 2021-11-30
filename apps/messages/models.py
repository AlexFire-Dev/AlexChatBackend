from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Conversation(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self) -> str:
        return f'{self.id}'


class ConversationMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='conversation_membership')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='conversation_members')

    def __str__(self) -> str:
        return f'{self.conversation}: {self.user}'


class ConversationMessage(models.Model):
    author = models.ForeignKey(ConversationMember, on_delete=models.CASCADE, related_name='member_messages')
    text = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.author}: {self.text}'
