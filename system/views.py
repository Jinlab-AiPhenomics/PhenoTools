from .models import *
from .serializers import *
import psutil
import pynvml
import platform
import datetime
from common.custommodelviewset import CustomModelViewSet
from rest_framework import status
from common.customresponse import CustomResponse
from common.config_parser import get_config, get_config_dict, set_config
import requests
import os
import shutil
import re
import torch, json
from django.core.mail import send_mail
from task.queue.tasks import add_task
from django_huey import result
from django.conf import settings


class SystemInfoViews(CustomModelViewSet):
    serializer_class = SystemInfoSerializer

    def get_latest_version(self):
        url = "http://phenotools.phenonet.org/version.json"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def list(self, request, *args, **kwargs):
        enable_mail = get_config("mail", "enable_mail") == "true"
        version_info = json.load(open(os.path.join(settings.BASE_DIR, "version.json")))
        server_version = version_info["server_version"]
        interface_version = version_info["interface_version"]
        try:
            latest_version = self.get_latest_version()
        except Exception as e:
            latest_version = {"server_version": "1.0.0", "interface_version": "1.0.0"}
        update = False
        # 判断版本
        if (
            server_version != latest_version["server_version"]
            or interface_version != latest_version["interface_version"]
        ):
            update = True

        # 获取CPU使用率
        # interval:间隔时间,percpu:每个cpu的使用率,percents:总的使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 获取硬盘使用情况
        # total:总容量,used:已用容量,free:剩余容量,percent:使用率
        disk_usage = psutil.disk_usage("/")
        disk_usage_free = round(disk_usage.free / (1024**3), 2)

        # 获取内存使用情况
        # total:总内存,available:可用内存,percent:使用率,used:已用内存,free:空闲内存
        memory = psutil.virtual_memory()
        memory_used_gb = round(memory.used / (1024**3), 2)
        memory_available_gb = round(memory.available / (1024**3), 2)

        # 计算系统负载
        # 1分钟内的负载,5分钟内的负载,15分钟内的负载
        load = psutil.getloadavg()

        # 计算磁盘IO
        disk_io = psutil.disk_io_counters()
        read_bytes = round(disk_io.read_bytes / (1024 * 1024), 2)
        write_bytes = round(disk_io.write_bytes / (1024 * 1024), 2)
        read_count = disk_io.read_count
        write_count = disk_io.write_count
        read_time = disk_io.read_time
        write_time = disk_io.write_time

        # 获取系统开机时间
        boot_time = psutil.boot_time()
        # 将时间戳转换为datetime类型
        boot_time_datetime = datetime.datetime.fromtimestamp(boot_time)
        # 将datetime类型的时间转换为字符串格式
        boot_time_str = boot_time_datetime.strftime("%Y-%m-%d %H:%M:%S")
        # 计算运行时长
        running_time = datetime.datetime.now() - datetime.datetime.fromtimestamp(
            boot_time
        )
        # 将时长转换为可读的格式
        running_time = str(running_time).split(".")[0]

        system = platform.system()  # 获取当前系统的标识符
        release = platform.release()

        gpu_available = True
        gpu_usage = []
        try:
            # 初始化NVML
            pynvml.nvmlInit()

            # 获取显卡数量
            num_gpus = pynvml.nvmlDeviceGetCount()
            # 获取每张显卡的占用情况
            for i in range(num_gpus):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                gpu_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_usage.append(gpu_info.gpu)

            if num_gpus > 0:
                try:
                    gpu = torch.cuda.is_available()
                except:
                    gpu = False
                if gpu == False:
                    gpu_available = False

            # 结束NVML
            pynvml.nvmlShutdown()
        except BaseException:
            gpu_available = False

        queue_status = True
        try:
            if os.path.exists("{}/logs/startup.log".format(settings.BASE_DIR)):
                queue_status = True
            else:
                queue_status = False
        except BaseException as e:
            queue_status = False

        system_data = {
            "update": update,
            "version": version_info,
            "enable_mail": bool(enable_mail),
            "gpu_available": gpu_available,
            "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_percent": cpu_percent,
            "disk_percent": disk_usage.percent,
            "disk_available": disk_usage_free,
            "ram_used": memory_used_gb,
            "ram_available": memory_available_gb,
            "ram_percent": memory.percent,
            "boot_time": boot_time_str,
            "running_time": running_time,
            "load": load[0],
            "read_bytes": read_bytes,
            "write_bytes": write_bytes,
            "read_count": read_count,
            "write_count": write_count,
            "read_time": read_time,
            "write_time": write_time,
            "system": system,
            "release": release,
            "gpu_usage": gpu_usage,
            "queue_status": queue_status,
            "storage_path": get_config("storage", "storage_path"),
        }

        return CustomResponse(
            data=system_data, code=200, msg="success", status=status.HTTP_200_OK
        )


class SystemSettingViews(CustomModelViewSet):
    serializer_class = SystemSettingSerializer

    def list(self, request, *args, **kwargs):
        storage_path = get_config("storage", "storage_path")
        mail = get_config_dict("mail")
        mail_server = mail["mail_server"]
        mail_port = mail["mail_port"]
        mail_username = mail["mail_username"]
        mail_password = mail["mail_password"]
        mail_from = mail["mail_from"]
        mail_ssl = mail["mail_ssl"]
        mail_default = mail["mail_default"]
        data = {
            "storage_path": storage_path,
            "mail_server": mail_server,
            "mail_port": mail_port,
            "mail_username": mail_username,
            "mail_password": mail_password,
            "mail_from": mail_from,
            "mail_ssl": mail_ssl,
            "mail_default": mail_default,
        }
        return CustomResponse(
            data=data, code=200, msg="success", status=status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        new_config = {"storage": {}, "mail": {}}

        if "storage_path" in data:
            new_config["storage"]["storage_path"] = data["storage_path"]
            folder_list = ["weights", "inference", "experiments"]
            for folder in folder_list:
                os.makedirs(os.path.join(data["storage_path"], folder), exist_ok=True)

        # 只添加存在的mail配置
        mail_keys = [
            "mail_server",
            "mail_port",
            "mail_username",
            "mail_password",
            "mail_from",
            "mail_ssl",
            "mail_default",
        ]
        for key in mail_keys:
            if key in data:
                new_config["mail"][key] = data[key]

        # 更新配置
        for index_1 in new_config:
            for index_2 in new_config[index_1]:
                set_config(index_1, index_2, new_config[index_1][index_2])

        return CustomResponse(
            data=data, code=200, msg="success", status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            send_mail(
                "Test email",
                "This is a test email.",
                data["mail_username"],
                [data["mail_default"]],
            )
        except Exception as e:
            return CustomResponse(
                data=str(e),
                code=500,
                msg="error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return CustomResponse(
            data="Send successfully",
            code=200,
            msg="success",
            status=status.HTTP_200_OK,
        )


class SystemLogViews(CustomModelViewSet):
    serializer_class = SystemLogSerializer
    default_page_number = 1
    default_page_size = 15
    current_path = os.path.dirname(__file__)
    parent_path = os.path.dirname(current_path)
    log_path = os.path.join(parent_path, "logs", "web")

    def list(self, request):
        get_type = request.query_params.get("t", None)
        pageNumber = self.default_page_number
        pageSize = self.default_page_size

        if "page" in request.query_params and request.query_params["page"] != "":
            pageNumber = int(request.query_params["page"])
        if (
            "page_size" in request.query_params
            and request.query_params["page_size"] != ""
        ):
            pageSize = int(request.query_params["page_size"])

        page_data, pagination = self.getAllLog(pageNumber, pageSize, get_type)
        return CustomResponse(
            data=page_data,
            code=200,
            msg="success",
            status=status.HTTP_200_OK,
            pagination=pagination,
        )

    def getAllLog(self, pageNumber, pageSize, get_type):
        log_list = os.listdir(os.path.join(self.parent_path, "logs", "web"))
        log_data = []
        if get_type == "detail":
            log_data = ""
        for log_file in log_list:
            with open(
                os.path.join(self.parent_path, "logs", "web", log_file),
                "r",
                encoding="utf-8",
            ) as f:
                lines = f.readlines()

            if get_type == "detail":
                log_data += "".join(lines)
                page_data = log_data
                pagination = {
                    "total": 0,
                    "total_page": 0,
                    "page_size": 0,
                    "page_num": 0,
                }
            else:
                errors = []
                for line_index, line in enumerate(lines):
                    if "ERROR" in line or "WARNING" in line:
                        errors.append((line_index, line))

                log_data = []
                for i in range(0, len(errors), 2):
                    start_index = errors[i][0]
                    end_index = errors[i][0] + 1
                    log_detail = lines[start_index:end_index]
                    match = re.search(
                        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+) \| (\w+\.\w+) \| (.*)",
                        log_detail[0],
                    )
                    if match:
                        log_data.append(
                            {
                                "log_time": match.group(1),
                                "log_level": match.group(2),
                                "logger_name": match.group(3),
                                "log_detail": log_detail,
                            }
                        )

                total = len(log_data)
                total_page = (total + pageSize - 1) // pageSize
                start = (pageNumber - 1) * pageSize
                end = start + pageSize
                page_data = log_data[start:end]
                pagination = {
                    "total": total,
                    "total_page": total_page,
                    "page_size": pageSize,
                    "page_num": pageNumber,
                }
        return page_data, pagination

    def delete(self, request, *args, **kwargs):
        shutil.rmtree(self.log_path)
        os.makedirs(self.log_path)
        return CustomResponse(code=200, msg="success", status=status.HTTP_200_OK)


class DownloadFileViews(CustomModelViewSet):
    serializer_class = SystemInfoSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if data["type"] == "init":
            os.makedirs(
                os.path.join(data["file_path"], "weights", "sr_g"), exist_ok=True
            )
            data["file_path"] = os.path.join(
                data["file_path"], "weights", "sr_g", data["file_name"]
            )
        try:
            queue_id = add_task(data, "add_download_file")
            queue_id = queue_id.id
        except Exception as e:
            return CustomResponse(
                code=500, msg=str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return CustomResponse(
            data={"task_id": queue_id},
            code=200,
            msg="success",
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        task_id = request.query_params["task_id"]
        task_progress = result(task_id)
        return CustomResponse(
            data=task_progress, code=200, msg="success", status=status.HTTP_200_OK
        )
