from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from subscriptions.services import get_user_tier
from .models import Video


@database_sync_to_async
def can_access(user, video_id):
    video = Video.objects.filter(pk=video_id).first()
    if video is None:
        return False
    return get_user_tier(user) >= video.required_tier


class VideoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.video_id = self.scope['url_route']['kwargs']['video_id']
        self.group_name = f'video_{self.video_id}'
        user = self.scope['user']

        if not user.is_authenticated or not await can_access(user, self.video_id):
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def video_event(self, event):
        await self.send_json({'event': event['event'], 'data': event['data']})