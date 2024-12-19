from django.conf import settings
from django.core.mail import send_mail
from common.config_parser import get_config
from django_huey import task
import os
from django_huey import on_startup, on_shutdown
from task.queue.utils import *


@task()
def add_task(conf, task_type):
    if task_type == "add_training_sr":
        msg = add_training_sr(conf)
    elif task_type == "add_prediction_sr":
        msg = add_prediction_sr(conf)
    elif task_type == "add_prediction_detection":
        msg = add_prediction_detection(conf)
    elif task_type == "multiscale_scaling":
        msg = add_multiscale_scaling(conf)
    elif task_type == "add_download_file":
        msg = add_download_file(conf)
    if task_type in ["add_training_sr", "add_prediction_sr"]:
        if conf["notice"]:
            try:
                send_mail(
                    "Task {} execution completed".format(conf["task_name"]),
                    msg,
                    settings.EMAIL_HOST_USER,
                    get_config("mail", "mail_default"),
                )
            except Exception:
                return {"code": 500, "msg": "Failed to send email"}
    msg = {"code": 200, "msg": "Task execution completed"}
    return msg


@on_startup()
def startup():
    with open("{}/logs/startup.log".format(settings.BASE_DIR), "w") as f:
        f.write("queue startup")
    try:
        os.remove("{}/logs/shutdown.log".format(settings.BASE_DIR))
    except BaseException:
        return {"status": 0, "msg": "Remove shutdown.log failed"}


@on_shutdown()
def shutdown():
    with open("{}/logs/shutdown.log".format(settings.BASE_DIR), "w") as f:
        f.write("queue shutdown")
    try:
        os.remove("{}/logs/startup.log".format(settings.BASE_DIR))
    except BaseException:
        return {"status": 0, "msg": "Remove startup.log failed"}
