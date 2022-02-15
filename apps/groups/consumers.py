import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.conf import settings

from aioapns import APNs, NotificationRequest, PushType
from django.core.paginator import Paginator
from rest_framework.authtoken.models import Token

from .serializers import *
from .models import *

from ..oauth.models import NotificationToken, AuthUser


class GroupConsumer(AsyncWebsocketConsumer):
    """ Group Consumer """

    connected_groups: [Group] = []

    async def connect(self):
        if self.scope['user'] == AnonymousUser() or self.scope['user'].online:
            return

        await self.accept()
        await self.setup()

        await self.channel_layer.group_add(
            'group_join',
            self.channel_name
        )

        for groupId in await self.getGroupIds():
            group_name = f'group_{groupId}'
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )

        await self.setOnline()
        for groupId in await self.getGroupIds():
            group_name = f'group_{groupId}'
            await self.channel_layer.group_send(
                group_name,
                {
                    'type': 'user_online',
                    'user_id': self.scope['user'].id,
                    'online': True
                }
            )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            'group_join',
            self.channel_name
        )

        await self.setOffline()
        for groupId in await self.getGroupIds():
            group_name = f'group_{groupId}'
            await self.channel_layer.group_send(
                group_name,
                {
                    'type': 'user_online',
                    'user_id': self.scope['user'].id,
                    'online': False
                }
            )

        for groupId in await self.getGroupIds():
            group_name = f'group_{groupId}'
            await self.channel_layer.group_discard(
                group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            text_data_json = json.loads(text_data)

            group_id = text_data_json['group_id']
            event = text_data_json['type']
        except:
            return

        # Проверка на правильность данных
        if not await self.checkMember(group_id):
            return

        # Управление сообщениями
        if event == 'message.load':
            """
            {
                "group_id": int,
                "type": "message.load"
            }
            """

            message_id = text_data_json.get('message_id')

            await self.send(text_data=json.dumps({
                'type': 'message.load',
                'messages': await self.getMessages(group_id=group_id, message_id=message_id)
            }))

        elif event == 'message.send':
            """
            {
                "group_id": int,
                "type": "message.send",
                "text": str
            }
            """

            try:
                message = text_data_json['text']
            except:
                return

            message = await self.createMessage(group_id=group_id, text=message)

            await self.channel_layer.group_send(
                f'group_{group_id}',
                {
                    'type': 'message_sent',
                    'message': message
                }
            )

            # Отправка уведомлений
            # query = await self.getNotificationTokenQuery(group_id=group_id)
            #
            # apns_key_client = APNs(
            #     key=os.path.join(settings.BASE_DIR, 'apps/groups/apple/apns-key.p8'),
            #     key_id=os.getenv('APNS_KEY_ID'),
            #     team_id=os.getenv('APNS_TEAM_ID'),
            #     topic=os.getenv('APNS_TOPIC'),
            #     use_sandbox=True,
            # )
            #
            # for obj in query:
            #     token = obj.key
            #
            #     request = NotificationRequest(
            #         device_token=token,
            #         message={
            #             'aps': {
            #                 'alert': message.text,
            #             }
            #         }
            #     )
            #
            #     try:
            #         await apns_key_client.send_notification(request)
            #     except:
            #         pass

    async def message_sent(self, event):
        """
        {
            "message": GroupMessage
        }
        """

        message: GroupMessage = event['message']

        await self.send(text_data=json.dumps({
            'type': 'message.sent',
            'message': await self.getMessage(message)
        }))

    async def user_online(self, event):
        """
        {
            "user_id": int,
            "online": bool
        }
        """

        if event['online']:
            await self.send(text_data=json.dumps({
                'type': 'member.online',
                'user_id': event['user_id']
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'member.offline',
                'user_id': event['user_id']
            }))

    async def group_join(self, event):
        """
        {
            "user_id": int,
            "group_id": int
        }
        """

        if event['user_id'] == self.scope['user'].id:
            group_id = event['group_id']

            if await self.checkMember(group_id):
                await self.addGroup(group_id)

                await self.channel_layer.group_add(
                    f'group_{group_id}',
                    self.channel_name
                )

                await self.send(text_data=json.dumps({
                    'type': 'group.join',
                    'group_id': group_id
                }))

    async def group_leave(self, event):
        """
        {
            "user_id": int,
            "group_id": int
        }
        """

        if event['user_id'] == self.scope['user'].id:
            group_id = event['group_id']

            await self.removeGroup(group_id)

            await self.channel_layer.group_discard(
                f'group_{group_id}',
                self.channel_name
            )

            await self.send(text_data=json.dumps({
                'type': 'group.leave',
                'group_id': group_id
            }))

    @database_sync_to_async
    def setOnline(self):
        self.scope['user'].online = True
        self.scope['user'].save()

    @database_sync_to_async
    def setOffline(self):
        self.scope['user'].online = False
        self.scope['user'].save()

    @database_sync_to_async
    def setup(self):
        self.connected_groups = []
        memberships = GroupMember.objects.filter(user=self.scope['user'], active=True)
        for membership in memberships:
            self.connected_groups.append(membership.group)

    @database_sync_to_async
    def addGroup(self, group_id):
        membership = GroupMember.objects.get(user=self.scope['user'], group_id=group_id, active=True)
        self.connected_groups.append(membership.group)

    @database_sync_to_async
    def removeGroup(self, group_id):
        for group in self.groups:
            if group_id == group.id:
                self.groups.remove(group)
                break

    @database_sync_to_async
    def getGroupIds(self) -> [int]:
        result = []
        for group in self.connected_groups:
            result.append(group.id)
        return result

    @database_sync_to_async
    def checkMember(self, group_id):
        try:
            return GroupMember.objects.get(user=self.scope['user'], group_id=group_id)
        except:
            return False

    @database_sync_to_async
    def getMessages(self, group_id, message_id=None):
        if message_id:
            messages = GroupMessage.objects.filter(author__group_id=group_id, id__lt=message_id).order_by('-id')
        else:
            messages = GroupMessage.objects.filter(author__group_id=group_id).order_by('-id')

        paginator = Paginator(messages, 15)
        serializer = GroupMessageSerializer(paginator.page(1), many=True)
        return serializer.data

    @database_sync_to_async
    def createMessage(self, group_id, text):
        author = GroupMember.objects.get(group_id=group_id, user=self.scope['user'], active=True)
        return GroupMessage.objects.create(author=author, text=text)

    @database_sync_to_async
    def getMessage(self, message: GroupMessage):
        serializer = GroupMessageSerializer(message)
        return serializer.data

    @database_sync_to_async
    def getNotificationTokenQuery(self, group_id):
        members = GroupMember.objects.filter(group_id=group_id, active=True)
        query = []

        for member in members:
            try:
                if member.user != self.scope['user']:
                    notification_token = NotificationToken.objects.get(user=member.user)
                    if notification_token.key != "NONE":
                        query.append(notification_token)
            except:
                pass

        return query
