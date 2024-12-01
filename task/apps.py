from django.apps import AppConfig


class taskConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "task"

    # def ready(self):
    #     from task.queue import singal_handler

    #     super().ready()
