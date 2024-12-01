#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 4/30/2024 3:22 PM
# @Author : Ruinan Zhang
# @File : customexception.py
# @Description:
from rest_framework import status
from rest_framework.views import exception_handler
from common.customresponse import CustomResponse
import traceback


def common_exception_handler(exc, context):
    response = exception_handler(exc, context)
    # if response is None:
    #     error_message = "System error: {}".format(str(exc))
    #     response = CustomResponse(
    #         data=str(error_message),
    #         code=500,
    #         msg="error",
    #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #     )
    #     traceback.print_exc()
    return response


class MannualTerminateException(Exception):
    def __init__(self, msg):
        self.msg = msg
