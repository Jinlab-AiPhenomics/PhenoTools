from task.models import *
from task.serializers import *
from model.serializers import *
from dataset.serializers import *
from rest_framework import status
from common.customresponse import CustomResponse
from common.custommodelviewset import CustomModelViewSet
from task.logger import TaskLogger
from django.conf import settings
from task.queue.tasks import add_task
from django.db.models import Q
from model.models import *
from dataset.models import *
import traceback, shutil, os
from common.config_parser import get_config
from django_huey import revoke_by_id


class PredictionTaskView(CustomModelViewSet):
    serializer_class = PredictionTaskSerializer
    default_page_number = 1
    default_page_size = 15

    def get_queryset(self, filter, pageNumber, pageSize, scope):
        queryset = PredictionTasks.objects.all().order_by("create_time")

        if filter != "":
            queryset = queryset.filter(filter)

        if scope != "all":
            start_index = (int(pageNumber) - 1) * int(pageSize)
            end_index = int(pageNumber) * int(pageSize)
            queryset = queryset[start_index:end_index]

        return queryset

    # 检索任务
    def list(self, request, *args, **kwargs):
        pageNumber = self.default_page_number
        pageSize = self.default_page_size

        if "page" in request.query_params and request.query_params["page"] != "":
            pageNumber = int(request.query_params["page"])
        if (
            "page_size" in request.query_params
            and request.query_params["page_size"] != ""
        ):
            pageSize = int(request.query_params["page_size"])

        # 搜索任务
        scope = "page_scope"
        filter = ""
        if "s" in request.query_params and request.query_params["s"] != "":
            filter = Q(task_name__contains=request.query_params["s"])
            scope = "all"

        queryset = self.filter_queryset(
            self.get_queryset(filter, pageNumber, pageSize, scope)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)

        queryset_total = self.get_queryset(filter, pageNumber, pageSize, "all")
        serializer_total = self.get_serializer(queryset_total, many=True)

        weight_ids = [data["weight_id"] for data in serializer.data]

        # 查询WeightHub模型中对应的weight_hubs
        weight_hubs = weightHub.objects.filter(weight_id__in=weight_ids).values(
            "weight_id", "network_id", "scale", "weight_name"
        )

        network_ids = [hub["network_id"] for hub in weight_hubs]

        # 查询NetworkHub模型中对应的network_hubs
        network_hubs = networkHub.objects.filter(network_id__in=network_ids).values(
            "network_id", "network_name"
        )

        network_hubs_dict = {
            hub["network_id"]: hub["network_name"] for hub in network_hubs
        }
        weight_hubs_dict = {hub["weight_id"]: hub["network_id"] for hub in weight_hubs}

        for data in serializer.data:
            weight_id = data["weight_id"]
            network_id = weight_hubs_dict.get(weight_id, None)
            if network_id is not None:
                network_name = network_hubs_dict.get(network_id, "N/A")
                data["network_name"] = network_name
            else:
                data["network_name"] = "N/A"

        sum_data = {"total": len(serializer_total.data), "data": serializer.data}
        return CustomResponse(
            data=sum_data, code=200, msg="success", status=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return CustomResponse(
            data=serializer.data, code=200, msg="success", status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["network_id"] = data["network_weight"][0]
        data["weight_id"] = data["network_weight"][1]
        log_path = "{}/logs/db/{}.log".format(settings.BASE_DIR, data["task_id"])

        logger = TaskLogger(data["task_id"], log_path=log_path)
        try:
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except Exception as e:
            error_message = "Failed to create the task {}, error: {}".format(
                data["task_id"], str(e)
            )
            logger.error(traceback.print_exc())
            return CustomResponse(
                data=str(e),
                code=500,
                msg="error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # 用于SR或表型提取的网络信息
        network_name = networkHub.objects.get(
            network_id=data["network_weight"][0]
        ).network_name
        data["network_name"] = network_name

        if "enhancement" in data.keys():
            if len(data["enhancement"]) > 0:
                for enhancement in data["enhancement"]:
                    # 用于SR网络信息
                    if enhancement == "phenosr":
                        network_id = weightHub.objects.get(
                            weight_id=data["srNetworkOptions"]
                        ).network_id
                        data["sr_network_name"] = networkHub.objects.get(
                            network_id=network_id
                        ).network_name

        if "sr" in data["task_type"]:
            task_type = "add_prediction_sr"
        elif "detection" in data["task_type"]:
            task_type = "add_prediction_detection"

        # 添加至任务队列
        try:
            queue_id = add_task(data, task_type)
            queue_id = queue_id.id
            PredictionTasks.objects.filter(task_id=data["task_id"]).update(
                queue_id=queue_id
            )
        except Exception as e:
            error_message = "Error assigning task ID {}, error {}".format(
                data["task_id"], str(e)
            )
            logger.error(error_message)
            return CustomResponse(
                data=[str(e)],
                code=500,
                msg="error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        success_message = (
            "Task created successfully with queue ID: {} and task ID: {}".format(
                queue_id, data["task_id"]
            )
        )
        logger.info(success_message)
        return CustomResponse(
            data={"task_id": data["task_id"]},
            code=200,
            msg="success",
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        task_ids = kwargs.get("pk")
        try:
            for task_id in task_ids.split(","):
                task_instance = PredictionTasks.objects.get(task_id=task_id)
                task_instance.delete()
                if task_instance.status == 0:
                    revoke_by_id(task_instance.celery_id)
                storage_path = get_config("storage", "storage_path")
                task_path = os.path.join(storage_path, "inference", task_id)
                try:
                    if os.path.exists(task_path):
                        shutil.rmtree(task_path)
                except PermissionError:
                    pass
        except PredictionTasks.DoesNotExist as e:
            return CustomResponse(
                data="Failed to delete task: {}".format(str(e)),
                code=500,
                msg="error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return CustomResponse(
            data="Delete successful", code=200, msg="success", status=status.HTTP_200_OK
        )
