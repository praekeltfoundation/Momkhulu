from celery.task import Task
from celery.utils.log import get_task_logger

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
