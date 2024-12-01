#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 4/30/2024 5:22 PM
# @Author : Ruinan Zhang
# @File : serializers.py
# @Description:

from rest_framework import serializers
from system.models import *


class SystemInfoSerializer(serializers.Serializer):
    class Meta:
        fields = "__all__"


class SystemSettingSerializer(serializers.Serializer):
    class Meta:
        fields = "__all__"


class SystemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = "__all__"
