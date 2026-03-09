"""Celery client for async task management."""

from celery import Celery

from core.config import settings


class CeleryClient:
    """Client class for Celery task queue operations."""

    def __init__(self):
        self._app = Celery(
            "worker",
            broker=settings.BROKER_URL,
            backend=settings.REDIS_BACKEND,
        )
        self._app.conf.task_routes = {
            "app.index_task.*": "index_queue",
            "app.search_task.*": "search_queue",
        }
        self._app.conf.update(
            {
                "broker_transport_options": {
                    "visibility_timeout": 9000,
                    "global_keyprefix": "queue_prefix:",
                }
            }
        )

    @property
    def app(self) -> Celery:
        """Get the Celery app instance."""
        return self._app

    def send_task(self, name: str, kwargs: dict, queue: str):
        """Send a task to the queue.

        Args:
            name: Task name.
            kwargs: Task keyword arguments.
            queue: Queue name.

        Returns:
            AsyncResult for the task.
        """
        return self._app.send_task(name, kwargs=kwargs, queue=queue)


# Singleton instance
celery_client = CeleryClient()
