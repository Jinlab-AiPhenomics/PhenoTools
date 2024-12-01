"""
Author: Ruinan Zhang
Date: 2023-05-21 18:49:17
LastEditTime: 2024-05-19 20:55:41
Description: 
Copyright (c) 2023 by Ruinan Zhang, All Rights Reserved. 
"""

from typing import Any
from file.serializers import *
from common.custommodelviewset import CustomModelViewSet
from rest_framework import status
from common.customresponse import CustomResponse
from common.config_parser import get_config
import os

"""
@description : 文件操作
"""


class FileViews(CustomModelViewSet):
    serializer_class = FileSerializer

    def __init__(self, **kwargs: Any) -> None:
        self.base_path = get_config("storage", "storage_path")

    def create(self, request):
        file_obj = request.FILES.get("file", None)
        # 上传图片的任务
        if request.POST.get("t") == "prediction":
            task_id = request.POST.get("task_id", None)
            storage_path = os.path.join(
                self.base_path, "inference", "{}".format(task_id), "lr"
            )
        else:
            # 上传权重等
            pass
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
        file_path = os.path.join(storage_path, file_obj.name)
        with open(file_path, "wb") as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        data = {}
        data["file_path"] = file_path
        return CustomResponse(
            code=200, msg="inference successful", data=data, status=status.HTTP_200_OK
        )

    def delete(self, request):
        if request.POST.get("t") == "prediction":
            task_id = request.POST.get("task_id", None)
            storage_path = os.path.join(
                self.base_path, "inference", "{}".format(task_id), "lr"
            )
        else:
            pass
        file_path = os.path.join(storage_path, request.POST.get("file_name"))
        if not os.path.exists(file_path):
            return CustomResponse(
                code=404,
                msg="error",
                data="File not found",
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            os.remove(file_path)
            data = {"file": file_path}
            return CustomResponse(
                data=data, code=200, msg="Delete success", status=status.HTTP_200_OK
            )
