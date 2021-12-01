import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from .models import *


class GroupConsumer(WebsocketConsumer):
    """ Group Consumer """

    group_id: int
    group_name: str

    group: Group
    member: GroupMember

    def connect(self):
        self.group_id = int(self.scope['url_route']['kwargs']['pk'])
        self.group_name = f'group_{self.group_id}'

        try:
            self.group = Group.objects.get(id=self.group_id)
            self.member = GroupMember.objects.get(user=self.scope['user'], group=self.group)
        except:
            return

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        try:
            text_data_json = json.loads(text_data)
            event = text_data_json['type']
        except:
            return

        if event == 'message.send':
            try:
                message = text_data_json['message']
            except:
                return

            message = GroupMessage.objects.create(author=self.member, text=message)

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'message_sent',
                    'message': message
                }
            )

    def message_sent(self, event):
        message: GroupMessage = event['message']

        self.send(text_data=json.dumps({
            'type': 'message.sent',
            'message': {
                'id': message.id,
                'author': {
                    'id': message.author.id,
                    'user': {
                        'email': message.author.user.email,
                        'username': message.author.user.username
                    }
                },
                'text': message.text,
                'created': message.created.strftime('%Y.%m.%d %H:%M'),
                'updated': message.updated.strftime('%Y.%m.%d %H:%M')
            }
        }))
