import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings

import asyncio
from aioapns import APNs, NotificationRequest, PushType

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
            await self.send(text_data=json.dumps({
                'type': 'message.load',
                'messages': await self.getMessages()
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
    def getMessages(self):
        messages = GroupMessage.objects.filter(author__group=self.group)
        serializer = GroupMessageSerializer(messages, many=True)
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
                    query.append(NotificationToken.objects.get(user=member.user))
            except:
                pass

        return query

    # @database_sync_to_async
    # def send_notifications(self, text):
    #     async def send_notifications(query, text):
    #         apns_key_client = APNs(
    #             key=os.path.join(settings.BASE_DIR, 'apps/groups/apple/apns-key.p8'),
    #             key_id=os.getenv('APNS_KEY_ID'),
    #             team_id=os.getenv('APNS_TEAM_ID'),
    #             topic=os.getenv('APNS_TOPIC'),
    #             use_sandbox=True,
    #         )
    #
    #         for obj in query:
    #             token = obj.key
    #
    #             request = NotificationRequest(
    #                 device_token=token,
    #                 message={
    #                     'aps': {
    #                         'alert': text,
    #                     }
    #                 }
    #             )
    #
    #             await apns_key_client.send_notification(request)
    #
    #     members = GroupMember.objects.filter(group=self.group, active=True, banned=False)
    #     query = []
    #
    #     for member in members:
    #         try:
    #             if member != self.member:
    #                 query.append(NotificationToken.objects.get(user=member.user))
    #         except:
    #             pass
    #
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    #     loop.run_until_complete(send_notifications(query, text))


# class GroupConsumer(WebsocketConsumer):
#     """ Group Consumer """
#
#     group_id: int
#     group_name: str
#
#     group: Group
#     member: GroupMember
#
#     def connect(self):
#         self.group_id = int(self.scope['url_route']['kwargs']['pk'])
#         self.group_name = f'group_{self.group_id}'
#
#         try:
#             self.group = Group.objects.get(id=self.group_id)
#             self.member = GroupMember.objects.get(user=self.scope['user'], group=self.group)
#         except:
#             return
#
#         async_to_sync(self.channel_layer.group_add)(
#             self.group_name,
#             self.channel_name
#         )
#
#         self.accept()
#
#     def disconnect(self, code):
#         async_to_sync(self.channel_layer.group_discard)(
#             self.group_name,
#             self.channel_name
#         )
#
#     def receive(self, text_data=None, bytes_data=None):
#         try:
#             text_data_json = json.loads(text_data)
#             event = text_data_json['type']
#         except:
#             return
#
#         if event == 'message.load':
#             messages = GroupMessage.objects.filter(author__group=self.group)
#             serializer = GroupMessageSerializer(messages, many=True)
#
#             self.send(text_data=json.dumps({
#                 'type': 'message.load',
#                 'messages': serializer.data
#             }))
#
#         elif event == 'message.send':
#             try:
#                 message = text_data_json['message']
#             except:
#                 return
#
#             message = GroupMessage.objects.create(author=self.member, text=message)
#
#             async_to_sync(self.channel_layer.group_send)(
#                 self.group_name,
#                 {
#                     'type': 'message_sent',
#                     'message': message
#                 }
#             )
#
#             members = GroupMember.objects.filter(group=self.group, active=True, banned=False)
#             query = []
#             for member in members:
#                 try:
#                     query.append(NotificationToken.objects.get(user=member.user))
#                 except:
#                     pass
#
#             for obj in query:
#                 if message.author.user != obj.user:
#                     token = obj.key
#
#                     if token:
#                         async def run():
#                             apns_key_client = APNs(
#                                 key=os.path.join(settings.BASE_DIR, 'apps/groups/apple/apns-key.p8'),
#                                 key_id=os.getenv('APNS_KEY_ID'),
#                                 team_id=os.getenv('APNS_TEAM_ID'),
#                                 topic=os.getenv('APNS_TOPIC'),
#                                 use_sandbox=True,
#                             )
#
#                             request = NotificationRequest(
#                                 device_token=token,
#                                 message={
#                                     'aps': {
#                                         'alert': message.text,
#                                     }
#                                 }
#                             )
#
#                             await apns_key_client.send_notification(request)
#
#                         loop = asyncio.new_event_loop()
#                         asyncio.set_event_loop(loop)
#                         loop.run_until_complete(run())
#
#     def message_sent(self, event):
#         message: GroupMessage = event['message']
#         serializer = GroupMessageSerializer(message)
#
#         self.send(text_data=json.dumps({
#             'type': 'message.sent',
#             'message': serializer.data
#         }))
