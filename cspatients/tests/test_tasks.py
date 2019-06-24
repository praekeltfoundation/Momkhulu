import json

import responses
from django.test import TestCase

from cspatients.tasks import send_wa_group_message


class SendGroupMessageTest(TestCase):
    def mock_send_message(self):
        responses.add(
            responses.POST,
            "https://fakewhatsapp/v1/messages",
            json={},
            status=200,
            match_querystring=True,
        )

    @responses.activate
    def test_send_wa_group_message(self):
        self.mock_send_message()

        send_wa_group_message("Test Message")

        wa_call = responses.calls[0]

        self.assertEqual(
            json.loads(wa_call.request.body),
            {
                "recipient_type": "group",
                "to": "the-group-id",
                "render_mentions": False,
                "type": "text",
                "text": {"body": "Test Message"},
            },
        )

        headers = wa_call.request.headers
        self.assertEqual(headers["Authorization"], "Bearer 123456")
        self.assertEqual(headers["Content-Type"], "application/json")
