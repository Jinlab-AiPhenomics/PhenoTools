from common.customexception import MannualTerminateException
from task.models import PredictionTasks, TrainingTasks
from task.logger import TaskLogger
from model.models import weightHub
from PIL import Image
import os
import uuid
import time
import glob
import shutil
import traceback, requests, hashlib
from django.utils import timezone
from modules.train import *
from modules.predict import *


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
        if "weight_md5" in conf.keys():
            md5 = hashlib.md5()
            with open(conf["file_path"], "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5.update(chunk)
            if md5.hexdigest() != conf["weight_md5"]:
                os.remove(conf["file_path"])
                return {"code": 500, "msg": "MD5 check failed"}
        if "task_type" in conf.keys() and conf["task_type"] == "download_weight":
            write_to_database(conf)
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
    shutil.copy(
        latest_net_g_weight_finetune,
        os.path.join(
            get_config("storage", "storage_path"),
            "weights",
            "sr_g",
            net_g_finetune_uuid + ".pth",
        ),
    )
    conf["weight_name"] = "{}_{}".format(conf["network_g"], time.time())
    conf["weight_id"] = net_g_finetune_uuid
    conf["type"] = "sr_g"
    conf["description"] = "Automatically import from the training task: {}".format(
        conf["task_name"]
    )
    write_to_database(conf)


def write_to_database(conf):
    if conf["type"] == "sr_g" or conf["type"] == "sr_d":
        weightHub.objects.create(
            weight_name=conf["weight_name"],
            weight_id=conf["weight_id"],
            network_id=conf["network_g_id"],
            weight_path=os.path.join(
                get_config("storage", "storage_path"),
                "weights",
                conf["type"],
                conf["weight_id"] + ".pth",
            ),
            weight_type=conf["type"],
            create_time=timezone.now().strftime("%Y-%m-%d %H:%M"),
            description=conf["description"],
        )


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
