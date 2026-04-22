from rq import Queue

from app.core.config import settings
from app.core.redis_client import redis_client

submission_queue = Queue(name=settings.redis_queue_name, connection=redis_client)


def enqueue_submission(submission_id: int) -> str:
    job = submission_queue.enqueue(
        "app.workers.submission_worker.process_submission_job",
        submission_id,
    )
    return job.id
