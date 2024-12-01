#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 4/30/2024 3:20 PM
# @Author : Ruinan Zhang
# @File : serializers.py
# @Description:


from rest_framework import serializers

class FileSerializer(serializers.Serializer):
    file = serializers.FileField()

class FileDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"

