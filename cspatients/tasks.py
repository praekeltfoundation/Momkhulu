import json
from urllib.parse import urljoin

import requests
from celery.exceptions import SoftTimeLimitExceeded
from celery.task import Task
from celery.utils.log import get_task_logger
from django.conf import settings
from requests import RequestException

from momkhulu.celery import app

from .util import send_consumers_table


class PostPatientUpdate(Task):
    """
    Task to kick off the frontend update after patient data has been updated.
    """

    name = "cspatients.tasks.post_patient_update"
    log = get_task_logger(__name__)

    def run(self, **kwargs):
        send_consumers_table()


post_patient_update = PostPatientUpdate()


@app.task(
    autoretry_for=(RequestException, SoftTimeLimitExceeded),
    retry_backoff=True,
    max_retries=15,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
    ignore_result=True,
)
def send_wa_group_message(message):
    headers = {
        "Authorization": "Bearer {}".format(settings.TURN_TOKEN),
        "Content-Type": "application/json",
    }

    response = requests.post(
        urljoin(settings.TURN_URL, "v1/messages"),
        headers=headers,
        data=json.dumps(
            {
                "recipient_type": "group",
                "to": settings.MOMKHULU_WA_GROUP_ID,
                "render_mentions": False,
                "type": "text",
                "text": {"body": message},
            }
        ),
    )
    response.raise_for_status()
    return response
