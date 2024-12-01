from dataset.models import *
from dataset.serializers import *
from rest_framework import status
from common.customresponse import CustomResponse
from common.custommodelviewset import CustomModelViewSet
from django.conf import settings
from django.db.models import Q, Count
from model.models import *
import traceback
import os
from task.queue.tasks import add_task

class DatasetView(CustomModelViewSet):
    serializer_class = DatasetSerializer
    default_page_number = 1
    default_page_size = 15

    def get_queryset(self, filter, pageNumber, pageSize, scope):
        queryset = Datasets.objects.all().order_by("create_time")

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

        filter = ""
        scope = "page_scope"
        if "s" in request.query_params and request.query_params["s"] != "":
            filter = Q(dataset_name__contains=request.query_params["s"])
            scope = "all"

        if (
            "t" in request.query_params
            and request.query_params["t"] != ""
            and request.query_params["t"] != "all"
        ):
            if request.query_params["t"] == "sr":
                filter = Q(task_type="sr")
            elif request.query_params["t"] == "pheno":
                filter = Q(task_type="pheno")

        queryset = self.filter_queryset(
            self.get_queryset(filter, pageNumber, pageSize, scope)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)

        if (
            "t" in request.query_params
            and request.query_params["t"] != ""
            and request.query_params["t"] != "all"
        ):
            category_return = {"training": [], "val": []}
            for data in serializer.data:
                if data["dataset_type"] == "training":
                    category_return["training"].append(data)
                elif data["dataset_type"] == "val":
                    category_return["val"].append(data)
            return CustomResponse(
                data=category_return, code=200, msg="success", status=status.HTTP_200_OK
            )

        sum_data = {"total": len(serializer.data), "data": serializer.data}
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
        if data["task_type"] == "sr":
            if not os.path.exists(data["dataset_path"]):
                return CustomResponse(
                    data="Dataset path does not exist",
                    code=500,
                    msg="error",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if data["dataset_type"] == "val":
                if "hr" not in os.listdir(
                    data["dataset_path"]
                ) or "lr" not in os.listdir(data["dataset_path"]):
                    return CustomResponse(
                        data="Dataset path does not contain hr or lr folder",
                        code=500,
                        msg="error",
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                hr_list = os.listdir(os.path.join(data["dataset_path"], "hr"))
                lr_list = os.listdir(os.path.join(data["dataset_path"], "lr"))
                if len(hr_list) != len(lr_list):
                    return CustomResponse(
                        data="The number of hr images and lr images does not match",
                        code=500,
                        msg="error",
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                if len(hr_list) == 0 or len(lr_list) == 0:
                    return CustomResponse(
                        data="The number of hr or lr images is 0",
                        code=500,
                        msg="error",
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            elif data["dataset_type"] == "training":
                if "hr" not in os.listdir(data["dataset_path"]):
                    return CustomResponse(
                        data="Dataset path does not contain hr folder",
                        code=500,
                        msg="error",
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                hr_list = os.listdir(os.path.join(data["dataset_path"], "hr"))
                if len(hr_list) == 0:
                    return CustomResponse(
                        data="The number of hr images is 0",
                        code=500,
                        msg="error",
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                if "multiscale" in data['preprocessing']:
                    add_task(data["dataset_path"], "multiscale_scaling")
                else:
                    with open(
                        os.path.join(data["dataset_path"], "meta_info.txt"), "w"
                    ) as f:
                        for hr in hr_list:
                            f.write(os.path.join("hr", hr) + "\n")

        try:
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except BaseException as e:
            return CustomResponse(
                data=str(e),
                code=500,
                msg="error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return CustomResponse(
            code=200,
            msg="success",
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        dataset_ids = kwargs.get("pk")
        try:
            for dataset_id in dataset_ids.split(","):
                dataset_instance = Datasets.objects.get(dataset_id=dataset_id)
                dataset_instance.delete()
        except Datasets.DoesNotExist as e:
            return CustomResponse(
                data="Failed to delete dataset: {}".format(str(e)),
                code=500,
                msg="error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return CustomResponse(
            data="Delete successful", code=200, msg="success", status=status.HTTP_200_OK
        )
