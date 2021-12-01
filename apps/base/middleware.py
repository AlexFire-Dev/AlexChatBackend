from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware


@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        try:
            token_key = dict(scope['headers'])[b'authorization'].decode('utf-8').split()
            token_key = token_key[1]
        except:
            token_key = None
        if token_key:
            scope['user'] = await get_user(token_key)
        else:
            scope['user'] = AnonymousUser
        return await super().__call__(scope, receive, send)
