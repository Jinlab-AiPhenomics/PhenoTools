from model.models import *
import os
from common.config_parser import get_config
from model.serializers import *
from rest_framework import status
from django.db.models import Q
from loguru import logger as loguru_logger
from common.customresponse import CustomResponse
from common.custommodelviewset import CustomModelViewSet
import shutil


class NetworkView(CustomModelViewSet):
    serializer_class = NetworkSerializer
    default_page_number = 1
    default_page_size = 15

    def get_queryset(self, filter, pageNumber, pageSize, scope):
        if scope == "all":
            if filter == "":
                queryset = networkHub.objects.all().order_by("create_time")
            else:
                queryset = networkHub.objects.filter(filter).order_by("create_time")
        else:
            queryset = networkHub.objects.all().order_by("create_time")[
                (int(pageNumber) - 1)
                * int(pageSize) : (int(pageNumber))
                * int(pageSize)
            ]
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
            filter = Q(network_name__contains=request.query_params["s"])
            scope = "all"

        if "t" in request.query_params and request.query_params["t"] != "":
            scope = "all"
            if request.query_params["t"] == "sr_g":
                filter = Q(network_type="sr_g")
            elif request.query_params["t"] == "sr_d":
                filter = Q(network_type="sr_d")
            elif request.query_params["t"] == "pheno":
                filter = Q(network_type="pheno")

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

        if "t" in request.query_params and request.query_params["t"] != "":
            data_class = {}
            if request.query_params["t"] == "sr_g":
                data_class = {"network_g": []}
                for data in serializer.data:
                    if data["network_type"] == "sr_g":
                        data_class["network_g"].append(data)
            elif request.query_params["t"] == "sr_d":
                data_class = {"network_d": []}
                for data in serializer.data:
                    if data["network_type"] == "sr_d":
                        data_class["network_d"].append(data)
            elif request.query_params["t"] == "pheno":
                data_class = {"pheno": []}
                for data in serializer.data:
                    if data["network_type"] == "pheno":
                        data_class["pheno"].append(data)
            sum_data = {"total": len(serializer_total.data), "data": data_class}
        else:
            sum_data = {"total": len(serializer_total.data), "data": serializer.data}

        return CustomResponse(
            data=sum_data, code=200, msg="success", status=status.HTTP_200_OK
        )


class WeightView(CustomModelViewSet):
    serializer_class = WeightSerializer
    default_page_number = 1
    default_page_size = 15

    def get_queryset(self, filter, pageNumber, pageSize, scope):
        if scope == "all":
            if filter == "":
                queryset = weightHub.objects.all().order_by("create_time")
            else:
                queryset = weightHub.objects.filter(filter).order_by("create_time")
        else:
            queryset = weightHub.objects.all().order_by("create_time")[
                (int(pageNumber) - 1)
                * int(pageSize) : (int(pageNumber))
                * int(pageSize)
            ]
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
            filter = Q(weight_name__contains=request.query_params["s"])
            scope = "all"

        if "t" in request.query_params:
            scope = "all"
            if request.query_params["t"] == "sr_g":
                filter = Q(weight_type="sr_g")
            elif request.query_params["t"] == "sr_d":
                filter = Q(weight_type="sr_d")
            elif request.query_params["t"] == "pheno":
                filter = Q(weight_type="pheno")

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
            "weight_id", "network_id"
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

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        initial_weight_path = data["weight_path"][0]
        data["weight_path"] = str(
            os.path.join(
                get_config("storage", "storage_path"),
                "weights",
                data["weight_type"],
                data["weight_id"] + ".pth",
            )
        )
        data["network_id"] = data["network_id"]
        data["weight_id"] = data["weight_id"]
        try:
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            if not os.path.exists(
                os.path.join(
                    get_config("storage", "storage_path"),
                    "weights",
                    data["weight_type"],
                )
            ):
                os.makedirs(
                    os.path.join(
                        get_config("storage", "storage_path"),
                        "weights",
                        data["weight_type"],
                    )
                )
            # 传递过来的是列表
            shutil.copyfile(
                initial_weight_path,
                os.path.join(
                    get_config("storage", "storage_path"),
                    "weights",
                    data["weight_type"],
                    data["weight_id"] + ".pth",
                ),
            )
        except Exception as e:
            error_message = "Failed to create the weight, error: {}".format(str(e))
            return CustomResponse(
                data=error_message,
                code=500,
                msg="error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        success_message = "Weights created successfully"
        return CustomResponse(
            data=success_message,
            code=200,
            msg="success",
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        weight_ids = kwargs.get("pk")
        try:
            for weight_id in weight_ids.split(","):
                weight_instance = weightHub.objects.get(weight_id=weight_id)
                weight_instance.delete()
                os.remove(weight_instance.weight_path)
        except weightHub.DoesNotExist as e:
            return CustomResponse(
                data="Failed to delete weight: {}".format(str(e)),
                code=500,
                msg="error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return CustomResponse(
            data="Delete successful", code=200, msg="success", status=status.HTTP_200_OK
        )


class NetworkWeightView(CustomModelViewSet):
    serializer_class = NetworkWeightSerializer

    def get_queryset(self, filter):
        queryset = networkHub.objects.filter(filter).order_by("create_time")
        return queryset

    def list(self, request, *args, **kwargs):

        filter = ""
        if "t" in request.query_params and request.query_params["t"] != "":
            filter = Q(network_type=request.query_params["t"])
            network_hubs = networkHub.objects.filter(filter).values(
                "network_id", "network_name"
            )
        else:
            network_hubs = networkHub.objects.all().values("network_id", "network_name")

        weight_hubs = weightHub.objects.all().values(
            "weight_id", "network_id", "weight_name", "scale"
        )
        networks = {hub["network_id"]: hub["network_name"] for hub in network_hubs}

        weights = []
        for network_id, network_name in networks.items():
            temp = {
                "value": network_id,
                "label": network_name,
                "children": [
                    {
                        "value": weight["weight_id"],
                        "label": weight["weight_name"],
                        "scale": weight["scale"],
                    }
                    for weight in weight_hubs
                    if weight["network_id"] == network_id
                ],
            }
            if temp["children"]:
                weights.append(temp)

        return_data = weights

        return CustomResponse(
            data=return_data, code=200, msg="success", status=status.HTTP_200_OK
        )
