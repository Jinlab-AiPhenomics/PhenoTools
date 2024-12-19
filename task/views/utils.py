from task.models import *
from task.serializers import *
from model.serializers import *
from dataset.serializers import *
from rest_framework import status
from common.customresponse import CustomResponse
from common.custommodelviewset import CustomModelViewSet
from django.conf import settings
from django.db.models import Q, Count
from common.config_parser import get_config
from model.models import *
from dataset.models import *
import os
from django_huey import revoke_by_id
from django.http import FileResponse


class TaskSummaryView(CustomModelViewSet):
    queryset = PredictionTasks.objects.all()
    serializer_class = TaskSummarySerializer

    def list(self, request, *args, **kwargs):
        prediction_tasks = PredictionTasks.objects.all()
        training_tasks = TrainingTasks.objects.all()

        prediction_data = self.get_task_status_counts(prediction_tasks)
        training_data = self.get_task_status_counts(training_tasks)

        data = {
            "queued": prediction_data["queued"] + training_data["queued"],
            "processing": prediction_data["processing"] + training_data["processing"],
            "finished": prediction_data["finished"] + training_data["finished"],
            "failed": prediction_data["failed"] + training_data["failed"],
        }

        return CustomResponse(
            data=data,
            code=200,
            msg="success",
            status=status.HTTP_200_OK,
        )

    def get_task_status_counts(self, tasks):
        return tasks.aggregate(
            queued=Count("task_id", filter=Q(status=0)),
            processing=Count("task_id", filter=Q(status=1)),
            finished=Count("task_id", filter=Q(status=2)),
            failed=Count("task_id", filter=Q(status=3)),
        )


class TaskLogView(CustomModelViewSet):
    serializer_class = TaskLogSerializer

    def list(self, request, *args, **kwargs):
        # 日志文件
        file_paths = []
        file_paths.append(
            os.path.join(
                settings.BASE_DIR,
                "logs",
                "db",
                "{}.log".format(request.GET.get("task_id")),
            )
        )
        if request.GET.get("t") == "training":
            file_paths.append(
                os.path.join(
                    get_config("storage", "storage_path"),
                    "experiments",
                    "{}".format(request.GET.get("task_id")),
                    "{}.log".format(request.GET.get("task_id")),
                )
            )
        else:
            file_paths.append(
                os.path.join(
                    get_config("storage", "storage_path"),
                    "inference",
                    "{}".format(request.GET.get("task_id")),
                    "{}.log".format(request.GET.get("task_id")),
                )
            )
        log_names = ["db_log", "queue_log"]
        logs = {}
        for file_path, log_name in zip(file_paths, log_names):
            try:
                with open(file_path, "r") as f:
                    logs[log_name] = f.read()
            except Exception as e:
                logs[log_name] = "No logs available for the {} of this task.".format(
                    log_name
                )

        # 可视化图片
        logs["visual_imgs"] = []
        # 模型训练
        if os.path.exists(
            os.path.join(
                get_config("storage", "storage_path"),
                "experiments",
                "{}".format(request.GET.get("task_id")),
                "visualization",
            )
        ):
            pass
        # 图像预测
        elif request.GET.get("t") == "sr":
            visual_imgs = []
            for img in os.listdir(
                os.path.join(
                    get_config("storage", "storage_path"),
                    "inference",
                    "{}".format(request.GET.get("task_id")),
                    "lr",
                )
            ):
                visual_imgs.append(img)
            logs["visual_imgs"] = {"lr": [], "sr": []}
            for i in visual_imgs:
                logs["visual_imgs"]["lr"].append(
                    {
                        "img_name": i,
                        "img_url": "http://127.0.0.1:8888/api/task/imgPreview/?task_id={}&folder={}&img_name={}&t=prediction&scale={}".format(
                            request.GET.get("task_id"),
                            "lr",
                            i,
                            request.GET.get("scale"),
                        ),
                    }
                )
                logs["visual_imgs"]["sr"].append(
                    {
                        "img_name": i,
                        "img_url": "http://127.0.0.1:8888/api/task/imgPreview/?task_id={}&folder={}&img_name={}&t=prediction".format(
                            request.GET.get("task_id"), "sr", i
                        ),
                    }
                )
        elif request.GET.get("t") == "spike_detection":
            visual_imgs = []
            for img in os.listdir(
                os.path.join(
                    get_config("storage", "storage_path"),
                    "inference",
                    "{}".format(request.GET.get("task_id")),
                    "result",
                )
            ):
                visual_imgs.append(img)
            logs["visual_imgs"] = {"result": []}
            for i in visual_imgs:
                logs["visual_imgs"]["result"].append(
                    {
                        "img_name": i,
                        "img_url": "http://127.0.0.1:8888/api/task/imgPreview/?task_id={}&folder={}&img_name={}&t=prediction".format(
                            request.GET.get("task_id"),
                            "result",
                            i,
                        ),
                    }
                )

        return CustomResponse(
            data=logs,
            code=200,
            msg="Success",
            status=status.HTTP_200_OK,
        )


import cv2 as cv
from django.http import HttpResponse


class ImagePreviewView(CustomModelViewSet):
    serializer_class = ImagePreviewSerializer

    def list(self, request, *args, **kwargs):
        if request.GET.get("t") == "training":
            img = cv.imread(
                os.path.join(
                    get_config("storage", "storage_path"),
                    "experiments",
                    "{}".format(request.GET.get("task_id")),
                    "visualization",
                    request.GET.get("folder"),
                    request.GET.get("img_name"),
                )
            )
        else:
            img = cv.imread(
                os.path.join(
                    get_config("storage", "storage_path"),
                    "inference",
                    "{}".format(request.GET.get("task_id")),
                    request.GET.get("folder"),
                    request.GET.get("img_name"),
                ),
            )
            if request.GET.get("scale") is not None:
                img = cv.resize(
                    img,
                    (
                        img.shape[1] * int(request.GET.get("scale")),
                        img.shape[0] * int(request.GET.get("scale")),
                    ),
                )
            _, buffer = cv.imencode(".jpg", img)
            img_bytes = buffer.tobytes()
        try:
            response = HttpResponse(img_bytes, content_type="image/jpeg")
            return response
        except FileNotFoundError:
            return CustomResponse(
                data="Image not found.",
                code=404,
                msg="error",
                status=status.HTTP_404_NOT_FOUND,
            )


class TaskConfigurationView(CustomModelViewSet):
    serializer_class = TaskConfigurationSerializer

    def list(self, request, *args, **kwargs):
        task_type = request.GET.get("t")
        network_g_id = request.GET.get("network_g_id")
        with open(
            os.path.join(
                settings.BASE_DIR,
                "task",
                "config",
                task_type,
                "finetune_{}.yaml".format(network_g_id),
            ),
            "r",
        ) as f:
            config = f.read()

        return CustomResponse(
            data=config,
            code=200,
            msg="Success",
            status=status.HTTP_200_OK,
        )


class StopTaskView(CustomModelViewSet):
    serializer_class = StopTaskSerializer

    def create(self, request, *args, **kwargs):
        task_status = request.data.get("status")
        if task_status == 0:
            revoke_by_id(request.data.get("queue_id"))
            handle_database = TrainingTasks.objects.get(
                task_id=request.data.get("task_id")
            )
            handle_database.status = 4
            handle_database.save()
        elif task_status == 1:
            task_id = request.data.get("task_id")
            save_path = os.path.join(
                get_config("storage", "storage_path"), "experiments", str(task_id)
            )
            # 生成标记任务停止的文件
            stop_file_path = os.path.join(save_path, "terminate.log")
            with open(stop_file_path, "w") as f:
                f.write("Manually terminate the task at {}".format(str(timezone.now())))
        return CustomResponse(
            data="Terminate successful.",
            code=200,
            msg="success",
            status=status.HTTP_200_OK,
        )
