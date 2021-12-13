import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.conf import settings

from .serializers import *
from .models import *

from ..oauth.models import NotificationToken, AuthUser


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
            import asyncio
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

            query = GroupMember.objects.filter(group=self.group).values('user').apns_token
            query = NotificationToken.objects.filter(user__groups__group_members=query)

            for obj in query:
                if message.author.user != obj.user:
                    token = obj.key

                    if token:
                        async def run():
                            apns_key_client = APNs(
                                key=os.path.join(settings.BASE_DIR, 'apps/groups/apple/apns-key.p8'),
                                key_id=os.getenv('APNS_KEY_ID'),
                                team_id=os.getenv('APNS_TEAM_ID'),
                                topic=os.getenv('APNS_TOPIC'),
                                use_sandbox=True,
                            )

                            request = NotificationRequest(
                                device_token=token,
                                message={
                                    'aps': {
                                        'alert': message.text,
                                    }
                                }
                            )

                            await apns_key_client.send_notification(request)

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(run())

    def message_sent(self, event):
        message: GroupMessage = event['message']
        serializer = GroupMessageSerializer(message)

        self.send(text_data=json.dumps({
            'type': 'message.sent',
            'message': serializer.data
        }))
