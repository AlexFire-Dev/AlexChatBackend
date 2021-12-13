import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from .serializers import *
from .models import *

from ..oauth.models import NotificationToken


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

        if event == 'message.load':
            messages = GroupMessage.objects.filter(author__group=self.group)
            serializer = GroupMessageSerializer(messages, many=True)

            self.send(text_data=json.dumps({
                'type': 'message.load',
                'messages': serializer.data
            }))

        elif event == 'message.send':
            from aioapns import APNs, NotificationRequest, PushType

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

            query = NotificationToken.objects.filter(user__groups=self.group)

            for obj in query:
                if message.author.user != obj.user:
                    try:
                        token = obj.key

                        if token:
                            apns_key_client = APNs(
                                key='/apps/oauth/apple/apns-key.p8',
                                key_id=os.getenv('APNS_KEY_ID'),
                                team_id=os.getenv('APNS_TEAM_ID'),
                                topic=os.getenv('APNS_TOPIC'),
                                use_sandbox=False,
                            )

                            request = NotificationRequest(
                                device_token=token,
                                message={
                                    'aps': {
                                        'alert': message.text,
                                    }
                                }
                            )

                            async_to_sync(apns_key_client.send_notification)(request)
                    except:
                        pass

    def message_sent(self, event):
        message: GroupMessage = event['message']
        serializer = GroupMessageSerializer(message)

        self.send(text_data=json.dumps({
            'type': 'message.sent',
            'message': serializer.data
        }))
