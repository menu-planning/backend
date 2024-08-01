from src.config.celery.app_worker import celery_app
from src.contexts.nutrition_assessment_and_planning.adapters.notifications import (
    EmailNotifications,
)


@celery_app.task(
    name="core.tasks.send_new_nutritionist_notification",
    ignore_result=True,
    bind=True,
)
def send_new_nutritionist_notification(self, user_id: str) -> None:
    EmailNotifications().send_new_nutritionist_notification(
        user_id=user_id,
    )
