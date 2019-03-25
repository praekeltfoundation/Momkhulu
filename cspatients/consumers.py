from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class ViewConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)("view", self.channel_name)
        self.accept()

    def view_update(self, event):
        self.send(text_data=event["content"])
