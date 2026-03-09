import logging
from celery import Celery

from core.config import settings

logger = logging.getLogger(__name__)


def get_celery_app():
    app = Celery("worker", broker=settings.BROKER_URL, backend=settings.REDIS_BACKEND)
    app.conf.task_routes = {
        "app.index_task.*": "index_queue",
        "app.search_task.*": "search_queue",
    }
    app.conf.update(
        {
            "broker_transport_options": {
                "visibility_timeout": 9000,
                "global_keyprefix": "queue_prefix:",
            }
        }
    )
    app.conf.include = [
        "tasks.index_task",
        "tasks.search_task",
    ]
    return app


celery_app = get_celery_app()

# Initialize PaddleOCR at worker startup
try:
    from core.paddleocr import get_paddle_ocr

    logger.info("Initializing PaddleOCR at worker startup...")
    get_paddle_ocr()
except Exception as e:
    logger.warning(
        f"PaddleOCR initialization failed (will be skipped for OCR tasks): {e}"
    )
