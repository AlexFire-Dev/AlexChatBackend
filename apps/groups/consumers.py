import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings

from aioapns import APNs, NotificationRequest, PushType
from django.core.paginator import Paginator

from .serializers import *
from .models import *

from ..oauth.models import NotificationToken, AuthUser


class GroupConsumer(AsyncWebsocketConsumer):
    """ Group Consumer """

    group_id: int
    group_name: str

    group: Group
    member: GroupMember

    async def connect(self):
        self.group_id = int(self.scope['url_route']['kwargs']['pk'])
        self.group_name = f'group_{self.group_id}'

        if not await self.checkUser():
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            text_data_json = json.loads(text_data)
            event = text_data_json['type']
        except:
            return

        if event == 'message.load':
            message_id = text_data_json.get('message_id')

            await self.send(text_data=json.dumps({
                'type': 'message.load',
                'messages': await self.getMessages(message_id=message_id)
            }))

        elif event == 'message.send':
            try:
                message = text_data_json['message']
            except:
                return

            message = await self.createMessage(message)

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'message_sent',
                    'message': message
                }
            )

            query = await self.getNotificationTokenQuery()

            apns_key_client = APNs(
                key=os.path.join(settings.BASE_DIR, 'apps/groups/apple/apns-key.p8'),
                key_id=os.getenv('APNS_KEY_ID'),
                team_id=os.getenv('APNS_TEAM_ID'),
                topic=os.getenv('APNS_TOPIC'),
                use_sandbox=True,
            )

            for obj in query:
                token = obj.key

                request = NotificationRequest(
                    device_token=token,
                    message={
                        'aps': {
                            'alert': message.text,
                        }
                    }
                )

                try:
                    await apns_key_client.send_notification(request)
                except:
                    pass

    async def message_sent(self, event):
        message: GroupMessage = event['message']

        await self.send(text_data=json.dumps({
            'type': 'message.sent',
            'message': await self.getMessage(message)
        }))

    @database_sync_to_async
    def checkUser(self) -> bool:
        try:
            self.group = Group.objects.get(id=self.group_id)
            self.member = GroupMember.objects.get(user=self.scope['user'], group=self.group)
            return True
        except:
            return False

    @database_sync_to_async
    def getMessages(self, message_id=None):
        if message_id:
            messages = GroupMessage.objects.filter(author__group=self.group, id__lt=message_id).order_by('-id')
        else:
            messages = GroupMessage.objects.filter(author__group=self.group).order_by('-id')

        paginator = Paginator(messages, 15)
        serializer = GroupMessageSerializer(paginator.page(1), many=True)
        return serializer.data

    @database_sync_to_async
    def createMessage(self, text):
        return GroupMessage.objects.create(author=self.member, text=text)

    @database_sync_to_async
    def getMessage(self, message: GroupMessage):
        serializer = GroupMessageSerializer(message)
        return serializer.data

    @database_sync_to_async
    def getNotificationTokenQuery(self):
        members = GroupMember.objects.filter(group=self.group, active=True, banned=False)
        query = []

        for member in members:
            try:
                if member != self.member:
                    notification_token = NotificationToken.objects.get(user=member.user)
                    if notification_token.key != "NONE":
                        query.append(notification_token)
            except:
                pass

        return query
