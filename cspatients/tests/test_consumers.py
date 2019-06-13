import pytest
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator

from cspatients.consumers import ViewConsumer


@pytest.mark.asyncio
async def test_view_consumer():
    communicator = WebsocketCommunicator(ViewConsumer, "/ws/cspatients/viewsocket/")

    connected, subprotocol = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "view", {"type": "view.update", "content": "Testing"}
    )

    response = await communicator.receive_from()
    assert response == "Testing"

    await communicator.disconnect()
