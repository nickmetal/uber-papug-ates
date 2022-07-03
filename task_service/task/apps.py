from django.apps import AppConfig
from task_service import container


class TaskConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "task"

    def ready(self):
        container.wire(modules=[".views", f"{self.name}.management.commands.consume_cud_events"])
