from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_video_event(video_id, event, data):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f'video_{video_id}',
        {'type': 'video.event', 'event': event, 'data': data},
    )

