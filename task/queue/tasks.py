from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from common.config_parser import get_config
from common.customexception import MannualTerminateException
from task.models import PredictionTasks, TrainingTasks
from task.logger import TaskLogger
from model.models import weightHub
from modules.train import *
from modules.predict import *
from django_huey import task
from PIL import Image
import os
import uuid
import time
import glob
import shutil
import traceback, requests
from django_huey import on_startup, on_shutdown


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


def add_training_sr(conf):
    task_id = conf["task_id"]
    try:
        handle_database = TrainingTasks.objects.get(task_id=task_id)
    except TrainingTasks.DoesNotExist:
        return "Task id does not exist"

    logger = TaskLogger(task_id, log_path=conf["log_path"])
    msg = "Task execution completed"

    try:
        handle_database.status = 1
        handle_database.start_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        handle_database.save()
        start_train_sr(conf)
        post_processing(conf)
        handle_database.status = 2
        handle_database.finish_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        handle_database.save()
    except MannualTerminateException:
        handle_database.status = 4
        handle_database.finish_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        handle_database.save()
        logger.error("Task info: \n{}".format(traceback.format_exc()))
        msg = "Manually terminate the task."
    except Exception:
        handle_database.status = 3
        handle_database.finish_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        handle_database.save()
        logger.error("Task error info: \n{}".format(traceback.format_exc()))
        msg = "Task execution failed."

    logger.info(msg)
    return msg


def add_prediction_sr(conf):
    task_id = conf["task_id"]
    handle_database = PredictionTasks.objects.get(task_id=task_id)
    log_path = os.path.join(
        get_config("storage", "storage_path"),
        "inference",
        "{}".format(task_id),
        "{}.log".format(task_id),
    )
    logger = TaskLogger(task_id, log_path=log_path)
    logger.info("Task info: \n{}".format(conf))
    msg = "Task execution completed"
    try:
        handle_database.status = 1
        handle_database.start_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        handle_database.save()
        start_predict_sr(conf, enhance=False)
        handle_database.status = 2
        handle_database.finish_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        handle_database.save()
    except BaseException:
        handle_database.status = 3
        handle_database.save()
        logger.error("Task error info: \n{}".format(traceback.format_exc()))
    logger.info(msg)
    return {"code": 200, "msg": msg}


def add_prediction_detection(conf):
    task_id = conf["task_id"]
    handle_database = PredictionTasks.objects.get(task_id=task_id)
    log_path = os.path.join(
        get_config("storage", "storage_path"),
        "inference",
        "{}".format(task_id),
        "{}.log".format(task_id),
    )
    logger = TaskLogger(task_id, log_path=log_path)
    logger.info("Task info: \n{}".format(conf))
    msg = "Task execution completed"
    try:
        handle_database.status = 1
        handle_database.start_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        handle_database.save()
        counting_number = start_predict_detection(conf)
        handle_database.status = 2
        handle_database.finish_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        handle_database.counting_number = counting_number
        handle_database.save()
    except BaseException:
        handle_database.status = 3
        handle_database.save()
        logger.error("Task error info: \n{}".format(traceback.format_exc()))
    logger.info(msg)
    return {"code": 200, "msg": msg}


def add_download_file(conf):
    try:
        response = requests.get(conf["file_url"], stream=True)
        response.raise_for_status()
        with open(conf["file_path"], "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.exceptions.HTTPError as http_err:
        return {"code": 500, "msg": f"HTTP error: {http_err}"}
    except requests.exceptions.ConnectionError as conn_err:
        return {"code": 500, "msg": f"Connection error: {conn_err}"}
    except requests.exceptions.Timeout as timeout_err:
        return {"code": 500, "msg": f"Timeout error: {timeout_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"code": 500, "msg": f"Request error: {req_err}"}
    except IOError as io_err:
        return {"code": 500, "msg": f"Write file error: {io_err}"}
    except Exception as e:
        return {"code": 500, "msg": f"Other error: {e}"}
    return {"code": 200, "msg": "success"}


def post_processing(conf):
    # latest_net_g_weight_train = os.path.join(
    #     get_config("storage", "storage_path"),
    #     "experiments",
    #     conf["task_id"],
    #     "models",
    #     "net_g_latest_train.pth",
    # )
    latest_net_g_weight_finetune = os.path.join(
        get_config("storage", "storage_path"),
        "experiments",
        conf["task_id"],
        "models",
        "net_g_latest_finetune.pth",
    )
    if not os.path.exists(
        os.path.join(
            get_config("storage", "storage_path"),
            "weights",
        )
    ):
        os.mkdir(
            os.path.join(
                get_config("storage", "storage_path"),
                "weights",
            )
        )

    net_g_finetune_uuid = str(uuid.uuid4())
    # shutil.copy(
    #     latest_net_g_weight_train,
    #     os.path.join(
    #         get_config("storage", "storage_path"), "weights", net_g_uuid + ".pth"
    #     ),
    # )
    shutil.copy(
        latest_net_g_weight_finetune,
        os.path.join(
            get_config("storage", "storage_path"),
            "weights",
            net_g_finetune_uuid + ".pth",
        ),
    )
    weightHub.objects.create(
        weight_name="{}_{}".format(conf["network_g"], time.time()),
        weight_id=net_g_finetune_uuid,
        network_id=conf["network_g_id"],
        weight_path=os.path.join(
            get_config("storage", "storage_path"),
            "weights",
            net_g_finetune_uuid + ".pth",
        ),
        weight_type="sr_g",
        create_time=timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="Automatically import from the training task: {}".format(
            conf["task_name"]
        ),
    )
    # weightHub.objects.create(
    #     weight_name="{}_{}".format(conf["network_d"], time.time()),
    #     weight_id=net_d_uuid,
    #     network_id=conf["network_d_id"],
    #     weight_path=os.path.join(
    #         get_config("storage", "storage_path"), "weights", net_d_uuid + ".pth"
    #     ),
    #     weight_type="sr_d",
    #     create_time=timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     description="Automatically import from the training task: {}.".format(
    #         conf["task_name"]
    #     ),
    # )


def add_multiscale_scaling(conf):
    scale_list = [0.875, 0.75, 0.625]
    shortest_edge = 512

    path_list = sorted(glob.glob(os.path.join(conf, "hr", "*")))
    os.makedirs(os.path.join(conf, "multiscale"), exist_ok=True)
    for path in path_list:
        basename = os.path.splitext(os.path.basename(path))[0]

        img = Image.open(path)
        width, height = img.size
        for idx, scale in enumerate(scale_list):
            rlt = img.resize(
                (int(width * scale), int(height * scale)), resample=Image.LANCZOS
            )
            rlt.save(
                os.path.join(os.path.join(conf, "multiscale"), f"{basename}T{idx}.png")
            )

        # save the smallest image which the shortest edge is 400
        if width < height:
            ratio = height / width
            width = shortest_edge
            height = int(width * ratio)
        else:
            ratio = width / height
            height = shortest_edge
            width = int(height * ratio)
        rlt = img.resize((int(width), int(height)), resample=Image.LANCZOS)
        rlt.save(
            os.path.join(os.path.join(conf, "multiscale"), f"{basename}T{idx + 1}.png")
        )

        multiscale_list = os.listdir(os.path.join(conf, "multiscale"))
        with open(os.path.join(conf, "meta_info.txt"), "w") as f:
            for multiscale in multiscale_list:
                f.write(os.path.join("multiscale", multiscale) + "\n")
