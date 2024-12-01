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
from common.config_parser import get_config
from model.models import *
from dataset.models import *
import traceback
import os
import yaml, shutil
from django_huey import revoke_by_id


class TrainingTaskView(CustomModelViewSet):
    serializer_class = TrainingTaskSerializer
    default_page_number = 1
    default_page_size = 15

    def get_queryset(self, filter, pageNumber, pageSize, scope):
        queryset = TrainingTasks.objects.all().order_by("create_time")

        if filter != "":
            queryset = queryset.filter(filter)

        if scope != "all":
            start_index = (int(pageNumber) - 1) * int(pageSize)
            end_index = int(pageNumber) * int(pageSize)
            queryset = queryset[start_index:end_index]

        return queryset

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

        for data in serializer.data:
            try:
                with open(
                    os.path.join(
                        get_config("storage", "storage_path"),
                        "experiments",
                        data["task_id"],
                        "train_{}.yaml".format(data["task_id"]),
                    ),
                    "r",
                ) as f:
                    config_file = f.read()
            except Exception as e:
                config_file = "No configuration file available for this task."
            data["config_file"] = config_file

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
        log_path = "{}/logs/db/{}.log".format(settings.BASE_DIR, data["task_id"])
        logger = TaskLogger(data["task_id"], log_path=log_path)

        try:
            sr_train_template, sr_finetune_template = self._get_sr_template(data)

            save_path = os.path.join(
                get_config("storage", "storage_path"),
                "experiments",
                str(data["task_id"]),
            )
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            with open(
                os.path.join(
                    save_path,
                    "train_{}.yaml".format(data["task_id"]),
                ),
                "w",
            ) as f:
                yaml.dump(sr_train_template, f, default_style="")
            with open(
                os.path.join(
                    save_path,
                    "finetune_{}.yaml".format(data["task_id"]),
                ),
                "w",
            ) as f:
                yaml.dump(sr_finetune_template, f, default_style="")

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            data["train_yaml_path"] = os.path.join(
                save_path, "train_{}.yaml".format(data["task_id"])
            )
            data["finetune_yaml_path"] = os.path.join(
                save_path, "finetune_{}.yaml".format(data["task_id"])
            )

            data["log_path"] = os.path.join(save_path, "{}.log".format(data["task_id"]))
            # add into the queue list
            queue_id = add_task(data, "add_training_sr")
            queue_id = queue_id.id
            TrainingTasks.objects.filter(task_id=data["task_id"]).update(
                queue_id=queue_id
            )

        except Exception as e:
            error_message = "Failed to create the task {}, error: {}".format(
                data["task_id"], str(e)
            )
            logger.error(traceback.print_exc())
            return CustomResponse(
                data=str(error_message),
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
            data=success_message,
            code=200,
            msg="success",
            status=status.HTTP_200_OK,
        )

    def _get_sr_template(self, data):
        if data["config_mode"] == "basic":
            with open(
                os.path.join(
                    settings.BASE_DIR,
                    "task",
                    "config",
                    data["task_type"],
                    "train_{}.yaml".format(data["network_g_id"]),
                ),
                "r",
            ) as f:
                sr_train_template = f.read()
            with open(
                os.path.join(
                    settings.BASE_DIR,
                    "task",
                    "config",
                    data["task_type"],
                    "finetune_{}.yaml".format(data["network_g_id"]),
                ),
                "r",
            ) as f:
                sr_finetune_template = f.read()

            sr_train_template = yaml.safe_load(sr_train_template)
            sr_finetune_template = yaml.safe_load(sr_finetune_template)

            # generate the configuration file for training
            queryset_dataset_training = Datasets.objects.get(
                dataset_id=data["dataset_training_id"]
            )
            serializer_dataset_training = DatasetSerializer(queryset_dataset_training)

            if len(data["dataset_val"]) > 0:
                queryset_dataset_val = Datasets.objects.get(
                    dataset_id=data["dataset_val_id"]
                )
                serializer_dataset_val = DatasetSerializer(queryset_dataset_val)
                sr_train_template["datasets"]["val"] = {}
                sr_train_template["datasets"]["val"].update(
                    {
                        "name": data["dataset_val"],
                        "type": "PairedImageDataset",
                        "dataroot_gt": os.path.join(
                            serializer_dataset_val.data["dataset_path"], "hr"
                        ),
                        "dataroot_lq": os.path.join(
                            serializer_dataset_val.data["dataset_path"], "lr"
                        ),
                        "io_backend": {"type": "disk"},
                    }
                )
                sr_finetune_template["datasets"]["val"] = {}
                sr_finetune_template["datasets"]["val"].update(
                    {
                        "name": data["dataset_val"],
                        "type": "PairedImageDataset",
                        "dataroot_gt": os.path.join(
                            serializer_dataset_val.data["dataset_path"], "hr"
                        ),
                        "dataroot_lq": os.path.join(
                            serializer_dataset_val.data["dataset_path"], "lr"
                        ),
                        "io_backend": {"type": "disk"},
                    }
                )
            sr_train_template["name"] = data["task_id"]
            sr_train_template["manual_seed"] = data["manual_seed"]
            sr_train_template["gt_size"] = int(data["gt_size"])
            sr_train_template["datasets"]["train"]["name"] = data["dataset_training"]
            sr_train_template["datasets"]["train"]["dataroot_gt"] = (
                serializer_dataset_training.data["dataset_path"]
            )
            sr_train_template["datasets"]["train"]["meta_info"] = os.path.join(
                serializer_dataset_training.data["dataset_path"], "meta_info.txt"
            )
            sr_train_template["datasets"]["train"]["gt_size"] = int(data["gt_size"])
            sr_train_template["datasets"]["train"]["num_worker_per_gpu"] = int(
                data["num_worker_per_gpu"]
            )
            sr_train_template["datasets"]["train"]["batch_size_per_gpu"] = int(
                data["batch_size_per_gpu"]
            )
            sr_train_template["scale"] = int(data["scale"])
            sr_train_template["train"]["optim_g"]["type"] = data["optim_g"]
            sr_train_template["train"]["scheduler"]["type"] = data["scheduler"]
            sr_train_template["train"]["total_iter"] = int(data["total_iter"])
            sr_train_template["logger"]["save_checkpoint_freq"] = int(
                data["save_checkpoint_freq"]
            )
            sr_train_template["path"]["root_path"] = get_config(
                "storage", "storage_path"
            )

            # finetune配置文件中的train数据集
            sr_finetune_template["name"] = data["task_id"]
            sr_finetune_template["manual_seed"] = data["manual_seed"]
            sr_finetune_template["gt_size"] = int(data["gt_size"])
            sr_finetune_template["datasets"]["train"]["name"] = data["dataset_training"]
            sr_finetune_template["datasets"]["train"]["dataroot_gt"] = (
                serializer_dataset_training.data["dataset_path"]
            )
            sr_finetune_template["datasets"]["train"]["meta_info"] = os.path.join(
                serializer_dataset_training.data["dataset_path"], "meta_info.txt"
            )
            sr_finetune_template["datasets"]["train"]["gt_size"] = int(data["gt_size"])
            sr_finetune_template["datasets"]["train"]["num_worker_per_gpu"] = int(
                data["num_worker_per_gpu"]
            )
            sr_finetune_template["datasets"]["train"]["batch_size_per_gpu"] = int(
                data["batch_size_per_gpu"]
            )
            sr_finetune_template["scale"] = int(data["scale"])
            sr_finetune_template["train"]["optim_g"]["type"] = data["optim_g"]
            sr_finetune_template["train"]["optim_d"]["type"] = data["optim_d"]
            sr_finetune_template["train"]["scheduler"]["type"] = data["scheduler"]
            sr_finetune_template["train"]["total_iter"] = int(data["total_iter"])
            sr_finetune_template["path"]["pretrain_network_g"] = os.path.join(
                get_config("storage", "storage_path"),
                "experiments",
                data["task_id"],
                "models",
                "net_g_latest_train.pth",
            )
            sr_finetune_template["logger"]["save_checkpoint_freq"] = int(
                data["save_checkpoint_freq"]
            )
            sr_finetune_template["path"]["root_path"] = get_config(
                "storage", "storage_path"
            )
            return sr_train_template, sr_finetune_template
        elif data["config_mode"] == "custom":
            sr_finetune_template = yaml.safe_load(data["custom_configuration"])
            sr_finetune_template["path"]["root_path"] = get_config(
                "storage", "storage_path"
            )
            return _, sr_finetune_template

    def destroy(self, request, *args, **kwargs):
        task_ids = kwargs.get("pk")
        try:
            for task_id in task_ids.split(","):
                task_instance = TrainingTasks.objects.get(task_id=task_id)
                task_instance.delete()
                if task_instance.status == 0:
                    revoke_by_id(task_instance.celery_id)
                task_path = os.path.join(
                    get_config("storage", "storage_path"), "experiments", task_id
                )
                try:
                    if os.path.exists(task_path):
                        shutil.rmtree(task_path)
                except PermissionError:
                    pass
        except TrainingTasks.DoesNotExist as e:
            return CustomResponse(
                data="Failed to delete task: {}".format(str(e)),
                code=500,
                msg="error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return CustomResponse(
            data="Delete successful", code=200, msg="success", status=status.HTTP_200_OK
        )
