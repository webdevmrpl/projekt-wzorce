import os
from celery import Celery
from kombu import Exchange, Queue

broker_url = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

app = Celery(
    "notes_celery",
    broker=broker_url,
    backend=backend_url,
)

app.conf.timezone = "Europe/Warsaw"

app.conf.task_queues = [
    Queue(
        "tasks",
        Exchange("tasks"),
        routing_key="tasks",
    )
]

app.autodiscover_tasks(["app.observers.task_observers"])
